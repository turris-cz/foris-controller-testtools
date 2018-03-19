#
# foris-controller-testtools
# Copyright (C) 2018 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#


import glob
import os
import pytest
import shutil
import subprocess

from .infrastructure import Infrastructure, SOCK_PATH, UBUS_PATH
from .utils import INIT_SCRIPT_TEST_DIR, set_userlists, set_languages

UCI_CONFIG_DIR_PATH = "/tmp/uci_configs"
FILE_ROOT_PATH = "/tmp/foris_files"
CLIENT_SOCKET_PATH = "/tmp/foris-controller-client-socket.soc"
REBOOT_INDICATOR_PATH = '/tmp/device-reboot-required'


def _override_exception(instructions):
    import inspect
    name = inspect.stack()[1][3]
    raise NotImplementedError("Override fixture '%s' in conftest.py: %s" % (name, instructions))


@pytest.fixture(scope="function")
def init_script_result():
    try:
        shutil.rmtree(INIT_SCRIPT_TEST_DIR, ignore_errors=True)
    except Exception:
        pass

    try:
        os.makedirs(INIT_SCRIPT_TEST_DIR)
    except Exception:
        pass

    yield INIT_SCRIPT_TEST_DIR

    return
    try:
        shutil.rmtree(INIT_SCRIPT_TEST_DIR, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture(scope="session")
def ubusd_acl_path():
    _override_exception("should return a path to ubus acl directory")


@pytest.fixture(scope="session")
def ubusd_test(ubusd_acl_path):
    ubusd_instance = subprocess.Popen(["ubusd", "-A", ubusd_acl_path, "-s", UBUS_PATH])
    yield ubusd_instance
    ubusd_instance.kill()
    try:
        os.unlink(SOCK_PATH)
    except Exception:
        pass


@pytest.fixture(scope="module")
def backend(backend_param):
    """ The backend name obtained via cmd line args"""
    return backend_param


@pytest.fixture(autouse=True)
def only_backends(request, backend):
    """ Set which backends should be used (others will be skipped)
    """
    if request.node.get_marker('only_backends'):
        if backend not in request.node.get_marker('only_backends').args[0]:
            pytest.skip("unsupported backend for this test '%s'" % backend)


@pytest.fixture(params=["unix-socket", "ubus"], scope="module")
def message_bus(request, backend):
    """ Message bus name (parametrized fixture) """
    return request.param


@pytest.fixture(autouse=True)
def only_message_buses(request, message_bus):
    """ Set which message buses should be used (others will be skipped)
    """
    if request.node.get_marker('only_message_buses'):
        if message_bus not in request.node.get_marker('only_message_buses').args[0]:
            pytest.skip("unsupported message bus for this test '%s'" % message_bus)


@pytest.fixture(scope="module")
def controller_modules():
    """ List of used modules. Note the if you want to limit module list,
        you can easilly override this fixture.
    """
    _override_exception("should return a list of required modules")


@pytest.fixture(scope="module")
def extra_module_paths():
    """ List of extra modules paths, (--extra-modules-paths) argument
    """
    return []  # by default return an empty list test should override this fixture


@pytest.fixture(scope="module")
def cmdline_script_root():
    _override_exception(
        "should return a path to a script root dir which are run within cmdline backend")


@pytest.fixture(scope="module")
def infrastructure(
    request, backend, message_bus, controller_modules, extra_module_paths, cmdline_script_root
):
    instance = Infrastructure(
        message_bus, backend, controller_modules, extra_module_paths, UCI_CONFIG_DIR_PATH,
        cmdline_script_root, FILE_ROOT_PATH, CLIENT_SOCKET_PATH,
        debug_output=request.config.getoption("--debug-output")
    )
    yield instance
    instance.exit()


@pytest.fixture(params=["threading", "multiprocessing"], scope="function")
def lock_backend(request):
    if request.param == "threading":
        import threading
        yield threading
    elif request.param == "multiprocessing":
        import multiprocessing
        yield multiprocessing


@pytest.fixture(scope="session")
def uci_config_default_path():
    _override_exception("should return a path to default uci config directory")


@pytest.fixture(autouse=True, scope="function")
def uci_configs_init(request, uci_config_default_path):
    """ Sets directory from where the uci configs should be looaded
        yields path to modified directory and path to original directory
    """
    if request.node.get_marker('uci_config_path'):
        dir_path = request.node.get_marker('uci_config_path').args[0]
    else:
        dir_path = uci_config_default_path

    # remove target dir
    shutil.rmtree(UCI_CONFIG_DIR_PATH, ignore_errors=True)
    try:
        os.makedirs(UCI_CONFIG_DIR_PATH)
    except IOError:
        pass

    # copy all the content of a directory
    for path in glob.glob("%s/*" % dir_path):
        shutil.copy(path, UCI_CONFIG_DIR_PATH)

    # yield paths
    yield UCI_CONFIG_DIR_PATH, dir_path

    # cleanup
    shutil.rmtree(UCI_CONFIG_DIR_PATH, ignore_errors=True)


@pytest.fixture(scope="module")
def file_root():
    _override_exception(
        "should return a path to a file root dir which are run within file backend")


@pytest.fixture(autouse=True, scope="function")
def file_root_init(request, file_root):
    if request.node.get_marker('file_root_path'):
        dir_path = request.node.get_marker('file_root_path').args[0]
    else:
        dir_path = file_root

    shutil.rmtree(FILE_ROOT_PATH, ignore_errors=True)
    shutil.copytree(dir_path, FILE_ROOT_PATH)

    yield FILE_ROOT_PATH, dir_path

    shutil.rmtree(FILE_ROOT_PATH, ignore_errors=True)


@pytest.fixture(scope="function")
def clean_reboot_indicator():
    try:
        os.unlink(REBOOT_INDICATOR_PATH)
    except Exception:
        pass

    yield REBOOT_INDICATOR_PATH

    try:
        os.unlink(REBOOT_INDICATOR_PATH)
    except Exception:
        pass


@pytest.fixture(scope="function")
def updater_userlists():
    import svupdater.lists
    try:
        os.unlink(svupdater.lists.LISTS_FILE_PATH)
    except Exception:
        pass

    set_userlists()
    yield svupdater.lists.LISTS_FILE_PATH

    try:
        os.unlink(svupdater.lists.LISTS_FILE_PATH)
    except Exception:
        pass


@pytest.fixture(scope="function")
def updater_languages():
    import svupdater.l10n
    try:
        os.unlink(svupdater.l10n.LANGS_FILE_PATH)
    except Exception:
        pass

    set_languages()
    yield svupdater.l10n.LANGS_FILE_PATH

    try:
        os.unlink(svupdater.l10n.LANGS_FILE_PATH)
    except Exception:
        pass
