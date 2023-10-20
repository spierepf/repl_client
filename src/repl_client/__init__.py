import ast
import hashlib
import os
import shutil
import time
import struct
import websocket
import serial


class BaseReplClient:
    def _import(self, module_name):
        self.exec(f"import {module_name}")

    def with_timeout(self, timeout, callback):
        previous_timeout = self.get_timeout()
        self.set_timeout(timeout)
        retval = callback()
        self.set_timeout(previous_timeout)
        return retval

    def assert_recv(self, expected):
        actual = self.recv(len(expected))
        if actual != expected:
            print()
            print('---')
            print(f"E: '{expected}'")
            print(f"A: '{actual}'")
            print('---')
            raise Exception()

    def assert_error(self, error):
        if error != b"":
            print(error)
            raise Exception()

    def __init__(self, connection, **kwargs):
        self.connection = connection

        self.establish_connection(**kwargs)
        self.recv_until(b">>> ")

        self.in_raw_repl_mode = False

    def enter_raw_repl_mode(self):
        if not self.in_raw_repl_mode:
            self.send("\x01")
            self.recv_until(b">")
            self.in_raw_repl_mode = True

    def enter_repl_mode(self):
        if self.in_raw_repl_mode:
            self.send("\x02")
            self.recv_until(b">>> ")
            self.in_raw_repl_mode = False

    def read_response_part(self):
        return self.recv_until(b"\x04")[:-1]

    def read_response(self):
        result = self.read_response_part()
        error = self.read_response_part()

        return result, error

    def exec(self, command):
        self.enter_raw_repl_mode()
        self.send_command(command)
        result, error = self.read_response()
        self.assert_recv(b">")
        return result, error

    def eval(self, expression):
        result, error = self.exec(f"print(repr({expression}), end='')")
        self.assert_error(error)
        return ast.literal_eval(result.decode('utf-8'))

    def remove(self, pathname):
        self._import("uos")
        result, error = self.exec(f"uos.remove('{pathname}')")
        self.assert_error(error)
        return result

    def sha256(self, pathname):
        chunk_size = 1024
        self._import("hashlib")
        self.exec("h = hashlib.sha256()")
        self.exec(f"f = open('{pathname}', 'rb')")

        self.exec(f"c = f.read({chunk_size})")
        while self.eval("bool(c)"):
            self.exec(f"h.update(c)")
            self.exec(f"c = f.read({chunk_size})")
        self.exec("f.close()")
        return self.eval("h.digest()")

    def mkdir(self, pathname):
        self._import("uos")
        result, error = self.exec(f"uos.mkdir('{pathname}')\r\n")
        self.assert_error(error)
        return result

    def isfile(self, pathname):
        self._import("uos")
        return self.eval(f"(uos.stat('{pathname}')[0] & 32768) == 32768")

    def isdir(self, pathname):
        self._import("uos")
        return self.eval(f"(uos.stat('{pathname}')[0] & 16384) == 16384")

    def exists(self, pathname):
        self._import("uos")
        self.exec(f"""
exists=True
try:
  uos.stat('{pathname}')
except:
  exists=False
""")
        return self.eval("exists")

    def listdir(self, pathname='/'):
        self._import("uos")
        return self.eval(f"uos.listdir('{pathname}')")

    def close(self):
        self.enter_repl_mode()
        self.connection.close()


class WebReplClient(BaseReplClient):
    WEBREPL_REQ_S = "<2sBBQLH64s"
    WEBREPL_PUT_FILE = 1
    WEBREPL_GET_FILE = 2
    WEBREPL_GET_VER = 3

    def set_timeout(self, timeout):
        self.connection.settimeout(timeout)

    def get_timeout(self):
        return self.connection.gettimeout()

    def recv(self, sz=-1):
        try:
            tmp = self.connection.recv()
            return tmp if str(type(tmp)) == "<class 'bytes'>" else tmp.encode("utf-8")
        except websocket.WebSocketException:
            return b''

    def recv_until(self, expected=b"/n"):
        buf = b""
        while not buf.endswith(expected):
            tmp = self.recv()
            if tmp == b'':
                break
            buf += tmp
        return buf

    def send(self, message):
        self.connection.send(message)

    def send_binary(self, message):
        self.connection.send_binary(message)

    def establish_connection(self, **kwargs):
        self.assert_recv(b"Password: ")
        self.send(kwargs['password'])
        self.send("\r\n")

    def send_command(self, command):
        chunk_size = 128
        for i in range(0, len(command), chunk_size):
            chunk = command[i:i+chunk_size]
            self.send(chunk)
            if i + chunk_size < len(command):
                time.sleep(0.3)
        self.send("\x04")
        self.assert_recv(b"OK")

    def read_resp(self):
        data = self.recv()
        sig, code = struct.unpack("<2sH", data)
        assert sig == b"WB"
        return code

    def begin_transfer(self, opcode, sz, b_pathname):
        self.enter_repl_mode()
        rec = struct.pack(self.WEBREPL_REQ_S, b"WA", opcode, 0, 0, sz, len(b_pathname), b_pathname)
        self.send_binary(rec)
        assert self.read_resp() == 0

    def put_file(self, pathname, content):
        self.begin_transfer(self.WEBREPL_PUT_FILE, len(content), pathname.encode('utf-8'))

        chunk_size = 1024
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            self.send_binary(chunk)
        assert self.read_resp() == 0

    def get_file(self, pathname):
        self.begin_transfer(self.WEBREPL_GET_FILE, 0, pathname.encode('utf-8'))

        content = b""
        while True:
            self.send_binary(b"\0")
            tmp = self.recv()
            (sz,) = struct.unpack("<H", tmp[:2])
            if sz == 0:
                break
            buf = tmp[2:]
            while len(buf) < sz:
                buf += self.recv()
            content += buf
        assert self.read_resp() == 0
        return content


class SerialReplClient(BaseReplClient):
    def set_timeout(self, timeout):
        self.connection.timeout = timeout

    def get_timeout(self):
        return self.connection.timeout

    def recv(self, sz=-1):
        if sz == -1:
            sz = self.connection.in_waiting
        if sz == 0:
            sz = 1
        return self.connection.read(sz)

    def recv_until(self, expected=b"/n"):
        return self.connection.read_until(expected)

    def send(self, message):
        self.connection.write(message.encode('utf-8'))

    def send_binary(self, message):
        self.connection.write(message)

    def pulse_dtr(self):
        self.connection.dtr = False
        time.sleep(0.01)
        self.connection.dtr = True

    def establish_connection(self, **kwargs):
        self.pulse_dtr()

    def send_command(self, command):
        self.send(command)
        self.send("\x04")
        self.assert_recv(b"OK")

    def put_file(self, pathname, content):
        self.exec(f"f = open('{pathname}', 'wb+')")
        chunk_size = 1024
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            self.exec(f"f.write({repr(chunk)})")
        self.exec("f.close()")

    def get_file(self, pathname):
        self.exec(f"f = open('{pathname}', 'rb')")
        content = b""
        chunk_size = 1024
        chunk = self.eval(f"f.read({chunk_size})")
        while chunk != b"":
            content += chunk
            chunk = self.eval(f"f.read({chunk_size})")
        self.exec("f.close()")
        return content

    def configure_wifi(self, ssid, psk):
        self._import("network")
        self.exec("sta_if = network.WLAN(network.STA_IF)")

        if not self.eval("sta_if.active()"):
            self.exec("sta_if.active(True)")

        if self.eval("sta_if.isconnected()") and self.eval("sta_if.config('essid')") != ssid:
            self.exec("sta_disconnect()")

        if not self.eval("sta_if.isconnected()"):
            self.exec(f"sta_if.connect('{ssid}', '{psk}')")

        while not self.eval("sta_if.isconnected()"):
            time.sleep(0.1)

        return self.eval("sta_if.ifconfig()[0]")

    def configure_webrepl(self, password):
        self._import("webrepl")
        self.exec(f"webrepl.start(password='{password}')")


class LocalClient:
    def __init__(self, root):
        self.root = root

    def mkdir(self, pathname):
        os.mkdir(self.root + pathname)

    def isdir(self, pathname):
        if os.path.exists(self.root + pathname):
            return os.path.isdir(self.root + pathname)
        else:
            raise Exception()

    def isfile(self, pathname):
        if os.path.exists(self.root + pathname):
            return os.path.isfile(self.root + pathname)
        else:
            raise Exception()

    def exists(self, pathname):
        return os.path.exists(self.root + pathname)

    def listdir(self, pathname="/"):
        return os.listdir(self.root + pathname)

    def put_file(self, pathname, content):
        with open(self.root + pathname, "wb+") as f:
            f.write(content)

    def get_file(self, pathname):
        with open(self.root + pathname, "rb") as f:
            return f.read()

    def remove(self, pathname):
        if os.path.exists(self.root + pathname):
            if os.path.isdir(self.root + pathname):
                shutil.rmtree(self.root + pathname)
            else:
                os.remove(self.root + pathname)

    def sha256(self, pathname):
        h = hashlib.sha256()
        with open(self.root + pathname, "rb") as f:
            h.update(f.read())
        return h.digest()

    def close(self):
        pass


class EndpointFactory:
    @staticmethod
    def _build_local_endpoint(name):
        return LocalClient(name)

    @staticmethod
    def _build_serial_endpoint(name, baud):
        connection = serial.Serial(name, baud)
        return SerialReplClient(connection)

    @staticmethod
    def _build_websocket_endpoint(name, password):
        connection = websocket.WebSocket()
        connection.connect(name)
        return WebReplClient(connection, password=password)

    def build_endpoint(self, name, args):
        if name.startswith("ws://"):
            password = None
            if len(args) > 1 and (args[0] == '-p' or args[0] == '--password'):
                args.pop(0)
                password = args.pop(0)
            if password is not None:
                return self._build_websocket_endpoint(name, password)
            else:
                raise RuntimeError(f"Websocket endpoint '{name}' missing password")
        elif name.startswith("/dev"):
            baud = 115200
            if len(args) > 1 and (args[0] == '-b' or args[0] == '--baud'):
                args.pop(0)
                baud = int(args.pop(0))
            return self._build_serial_endpoint(name, baud)
        else:
            if os.path.isdir(name):
                return self._build_local_endpoint(name)
            else:
                raise RuntimeError(f"Local endpoint '{name}' is not a directory")
