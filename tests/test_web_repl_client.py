import pytest
import time

from .common import web_client, serial_client
from .credentials import WIFI_CREDENTIALS

from .filesystem_suite import test_mkdir, test_isdir, test_isfile, test_listdir, test_remove_dir, test_remove_file, \
    test_put_file, test_put_file_get_file_remove, test_sha256, test_readfile_dne, test_listdir_dne, test_listdir_root, \
    test_large_file, test_exists


@pytest.fixture
def client():
    with web_client(WIFI_CREDENTIALS['ssid'], WIFI_CREDENTIALS['psk']) as retval:
        yield retval


def test_recv_with_timeout(client):
    t0 = time.time()
    retval = client.with_timeout(1.0, lambda: client.recv())
    t = time.time() - t0
    assert retval == b''
    assert t > 0.99


def test_recv_until_with_timeout(client):
    t0 = time.time()
    retval = client.with_timeout(1.0, lambda: client.recv_until(b'>>> '))
    t = time.time() - t0
    assert retval == b''
    assert t > 0.99


def test_both_modes(client):
    assert not client.in_raw_repl_mode
    client.enter_raw_repl_mode()
    assert client.in_raw_repl_mode
    client.enter_repl_mode()
    assert not client.in_raw_repl_mode


def test_exec(client):
    result, error = client.exec("print(repr(1+2), end='')")

    assert result == b"3"
    assert error == b""


def test_exception(client):
    result, error = client.exec("raise(Exception())")

    assert result == b""
    assert error != b""


def test_eval(client):
    assert client.eval("1+2") == 3
