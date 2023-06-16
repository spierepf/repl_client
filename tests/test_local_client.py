import shutil

import pytest
import tempfile

from .context import repl_client

from .filesystem_suite import test_mkdir, test_isdir, test_isfile, test_listdir, test_remove_dir, test_remove_file, \
    test_put_file, test_put_file_get_file_remove, test_sha256, test_readfile_dne, test_listdir_dne, test_listdir_root, \
    test_large_file, test_exists


@pytest.fixture
def client():
    path = tempfile.mkdtemp()
    with open(path + "/boot.py", "wb+") as f:
        pass
    retval = repl_client.LocalClient(path)
    yield retval
    shutil.rmtree(path)
    retval.close()
