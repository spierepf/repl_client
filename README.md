# repl_client
A client for micropython's REPL


## Running the automated tests

The tests are implemented using `pytest`, and need a small amount of local configuration. In particular,
the tests need to know how to connect to wifi in order to test the websocket implementation of the library.

To configure this, create a file entitled `credentials.py` inside the `test` directory of the following
form:

```python
WIFI_CREDENTIALS={
    "ssid": "<<SSID>>",
    "psk": "<<PSK>>"
}
```

The tests assume a Linux environment (I don't have a Mac, or Windows machine) and assume that `/dev/USB0`
is the serial port running at 115200bps connected to a device running micropython.

Finally, once you've got all your ducks in a row, you can type:

```bash
$ pytest
```

and you should have a green bar.

Please note that some of the tests (particularly the websocket ones) take a fair amount of time. This is
because each test has a fair amount of handshaking to do, to bring the device to a known state.