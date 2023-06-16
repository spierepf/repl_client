import random
import string

import pytest
import os
import hashlib


@pytest.mark.parametrize("content", [
    b'Hello World!',
    b'Hello\tWorld!',
    b'Hello World!\n',
    b'Hello "World"!',
    b"Hello 'World'!",
])
def test_put_file_get_file_remove(client, content):
    client.put_file('/test.txt', content)
    assert content == client.get_file('/test.txt')
    client.remove('/test.txt')


def test_sha256(client):
    content = bytearray(os.urandom(256))
    sha256_hash = hashlib.sha256(content).digest()
    client.put_file('/test.txt', content)
    assert sha256_hash == client.sha256('/test.txt')
    client.remove('/test.txt')


def test_isfile(client):
    assert client.isfile("/boot.py")
    assert not client.isfile("/")
    with pytest.raises(Exception):
        client.isfile('/dne')


def test_isdir(client):
    assert not client.isdir("/boot.py")
    assert client.isdir("/")
    with pytest.raises(Exception):
        client.isdir('/dne')


def test_exists(client):
    assert client.exists('/boot.py')
    assert not client.exists('/dne')


def test_listdir(client):
    assert 'boot.py' in client.listdir()


def test_listdir_root(client):
    assert 'boot.py' in client.listdir('/')


def test_listdir_dne(client):
    with pytest.raises(Exception):
        client.listdir('/dne')


def test_readfile_dne(client):
    with pytest.raises(Exception):
        client.readfile('/dne')


def test_put_file(client):
    client.put_file('/test.txt', b'')
    assert 'test.txt' in client.listdir('/')
    assert client.isfile('/test.txt')
    client.remove('/test.txt')


def test_mkdir(client):
    client.mkdir('/test')
    assert 'test' in client.listdir('/')
    assert client.isdir('/test')
    client.remove('/test')


def test_remove_file(client):
    client.put_file('/test.txt', b'')
    client.remove('/test.txt')
    assert 'test.txt' not in client.listdir('/')


def test_remove_dir(client):
    client.mkdir('/test')
    client.remove('/test')
    assert 'test' not in client.listdir('/')


def test_large_file(client):
    body = ''.join(random.choice(string.ascii_lowercase) for i in range(1024*256)).encode('utf-8')
    client.put_file('/test.txt', body)
    assert client.get_file('/test.txt') == body
    client.remove('/test.txt')