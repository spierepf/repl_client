from contextlib import contextmanager
import serial
import websocket

from .context import repl_client
from .config import SERIAL_CONFIG


@contextmanager
def serial_client(port, baud):
    connection = serial.Serial(port, baud)
    retval = repl_client.SerialReplClient(connection)
    yield retval
    retval.close()


@contextmanager
def web_client(ssid, psk):
    with serial_client(SERIAL_CONFIG['port'], SERIAL_CONFIG['baud']) as _serial_client:
        ip = _serial_client.configure_wifi(ssid, psk)
        _serial_client.configure_webrepl('password')

        connection = websocket.WebSocket()
        connection.connect(f'ws://{ip}:8266/')
        retval = repl_client.WebReplClient(connection, password='password')
        yield retval
        retval.close()
