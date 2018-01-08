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

from multiprocessing import Lock

from .infrastructure import Infrastructure, SOCK_PATH, UBUS_PATH


UCI_CONFIG_DIR_PATH = "/tmp/uci_configs"


notifications_lock = Lock()


@pytest.fixture(scope="session")
def ubusd_test():
    ubusd_instance = subprocess.Popen(["ubusd", "-A", "tests/ubus-acl", "-s", UBUS_PATH])
    yield ubusd_instance
    ubusd_instance.kill()
    try:
        os.unlink(SOCK_PATH)
    except:
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
    return [
        "about", "data_collect", "web", "dns", "maintain", "password", "updater", "lan"
    ]


@pytest.fixture(scope="module")
def extra_module_paths():
    """ List of extra modules paths, (--extra-modules-paths) argument
    """
    return []  # by default return an empty list test should override this fixture


@pytest.fixture(scope="module")
def infrastructure(request, backend, message_bus, controller_modules, extra_module_paths):
    instance = Infrastructure(
        message_bus, backend, controller_modules, extra_module_paths, UCI_CONFIG_DIR_PATH,
        request.config.getoption("--debug-output")
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


@pytest.fixture(autouse=True, scope="function")
def uci_configs_init(request):
    """ Sets directory from where the uci configs should be looaded
        yields path to modified directory and path to original directory
    """
    if request.node.get_marker('uci_config_path'):
        dir_path = request.node.get_marker('uci_config_path').args[0]
    else:
        dir_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "uci_configs", "defaults"
        )

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
