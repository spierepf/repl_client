import tempfile
from unittest.mock import Mock

import pytest

from .context import repl_client


def test_build_endpoint_local():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_local_end_point = Mock()
    endpoint_factory._build_local_endpoint = mock_build_local_end_point

    args = []
    endpoint_factory.build_endpoint("/tmp", args)

    mock_build_local_end_point.assert_called_with("/tmp")
    assert args == []


def test_build_endpoint_local_with_non_directory_fails():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_local_end_point = Mock()
    endpoint_factory._build_local_endpoint = mock_build_local_end_point

    with tempfile.NamedTemporaryFile() as fp:
        args = []
        with pytest.raises(RuntimeError, match=r".*'" + fp.name + "'.*"):
            endpoint_factory.build_endpoint(fp.name, args)


def test_build_endpoint_serial_with_default_baud():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_serial_end_point = Mock()
    endpoint_factory._build_serial_endpoint = mock_build_serial_end_point

    args = []
    endpoint_factory.build_endpoint("/dev/ttyUSB0", args)

    mock_build_serial_end_point.assert_called_with("/dev/ttyUSB0", 115200)
    assert args == []


def test_build_endpoint_serial_with_specified_baud_short_option():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_serial_end_point = Mock()
    endpoint_factory._build_serial_endpoint = mock_build_serial_end_point

    args = ['-b', '9600']
    endpoint_factory.build_endpoint("/dev/ttyUSB0", args)

    mock_build_serial_end_point.assert_called_with("/dev/ttyUSB0", 9600)
    assert args == []


def test_build_endpoint_serial_with_specified_baud_long_option():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_serial_end_point = Mock()
    endpoint_factory._build_serial_endpoint = mock_build_serial_end_point

    args = ['--baud', '9600']
    endpoint_factory.build_endpoint("/dev/ttyUSB0", args)

    mock_build_serial_end_point.assert_called_with("/dev/ttyUSB0", 9600)
    assert args == []


def test_build_endpoint_websocket_with_specified_password_short_option():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_websocket_end_point = Mock()
    endpoint_factory._build_websocket_endpoint = mock_build_websocket_end_point

    args = ['-p', 'some_password']
    endpoint_factory.build_endpoint("ws://127.0.0.1:8266/", args)

    mock_build_websocket_end_point.assert_called_with("ws://127.0.0.1:8266/", "some_password")
    assert args == []


def test_build_endpoint_websocket_with_specified_password_long_option():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_websocket_end_point = Mock()
    endpoint_factory._build_websocket_endpoint = mock_build_websocket_end_point

    args = ['--password', 'some_password']
    endpoint_factory.build_endpoint("ws://127.0.0.1:8266/", args)

    mock_build_websocket_end_point.assert_called_with("ws://127.0.0.1:8266/", "some_password")
    assert args == []


def test_build_endpoint_websocket_without_password_fails():
    endpoint_factory = repl_client.EndpointFactory()
    mock_build_websocket_end_point = Mock()
    endpoint_factory._build_websocket_endpoint = mock_build_websocket_end_point

    args = []
    with pytest.raises(RuntimeError, match=r".*'ws://127.0.0.1:8266/'.*"):
        endpoint_factory.build_endpoint("ws://127.0.0.1:8266/", args)
