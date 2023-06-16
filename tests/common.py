from contextlib import contextmanager
import serial
import websocket

from .context import repl_client


@contextmanager
def serial_client(port="/dev/ttyUSB0", baud=115200):
    connection = serial.Serial(port, baud)
    retval = repl_client.SerialReplClient(connection)
    yield retval
    retval.close()


@contextmanager
def web_client(ssid, psk):
    with serial_client() as _serial_client:
        ip = _serial_client.configure_wifi(ssid, psk)
        _serial_client.configure_webrepl('password')

        connection = websocket.WebSocket()
        connection.connect(f'ws://{ip}:8266/')
        retval = repl_client.WebReplClient(connection, password='password')
        yield retval
        retval.close()
