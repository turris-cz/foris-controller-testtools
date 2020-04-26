#
# foris-controller-testtools
# Copyright (C) 2018, 2020 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import json
import os
import pytest
import shutil
import subprocess
import textwrap
import warnings

from .infrastructure import (
    MqttInfrastructure,
    UbusInfrastructure,
    UnixSocketInfrastructure,
    SOCK_PATH,
    UBUS_PATH,
    MQTT_HOST,
    MQTT_PORT,
)
from .utils import (
    INIT_SCRIPT_TEST_DIR,
    set_package_lists,
    set_languages,
    FileFaker,
    SH_CALLED_FILE,
    REBOOT_CALLED_FILE,
    NETWORK_RESTART_CALLED_FILE,
    LIGHTTPD_RESTART_CALLED_FILE,
)


UCI_CONFIG_DIR_PATH = "/tmp/uci_configs"
FILE_ROOT_PATH = "/tmp/foris_files"
CLIENT_SOCKET_PATH = "/tmp/foris-controller-client-socket.soc"
REBOOT_INDICATOR_PATH = "/tmp/device-reboot-required"


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

    try:
        shutil.rmtree(INIT_SCRIPT_TEST_DIR, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture(scope="session")
def ubusd_test():
    warnings.warn(
        "Fixture 'ubusd_test' is deprecated. "
        "Infrastructure should handle starting and stopping ubusd. "
        "Note that this fixture will be removed in the future",
        DeprecationWarning,
    )


@pytest.fixture(scope="session")
def mosquitto_test(request):
    warnings.warn(
        "Fixture 'mosquitto_test' is deprecated. "
        "Infrastructure should handle starting and stopping mosquitto. "
        "Note that this fixture will be removed in the future",
        DeprecationWarning,
    )


@pytest.fixture(scope="session")
def start_buses(ubusd_test, mosquitto_test):
    warnings.warn(
        "Fixture 'start_buses' is deprecated. "
        "Infrastructure should handle starting and stopping buses. "
        "Note that this fixture will be removed in the future",
        DeprecationWarning,
    )


@pytest.fixture(scope="module")
def backend(backend_param):
    """ The backend name obtained via cmd line args"""
    return backend_param


@pytest.fixture(autouse=True)
def only_backends(request, backend):
    """ Set which backends should be used (others will be skipped)
    """
    if request.node.get_closest_marker("only_backends"):
        if backend not in request.node.get_closest_marker("only_backends").args[0]:
            pytest.skip("unsupported backend for this test '%s'" % backend)


@pytest.fixture(scope="module")
def message_bus(message_bus_param):
    """ Message bus name obtained via cmdline"""
    return message_bus_param


@pytest.fixture(autouse=True)
def only_message_buses(request, message_bus):
    """ Set which message buses should be used (others will be skipped)
    """
    if request.node.get_closest_marker("only_message_buses"):
        if message_bus not in request.node.get_closest_marker("only_message_buses").args[0]:
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
def env_overrides():
    """ List of env variables to be used with foris-controller (running within Infrastructure)
    """
    return {}  # by default return an empty dict test should override this fixture


@pytest.fixture(scope="module")
def cmdline_script_root():
    _override_exception(
        "should return a path to a script root dir which are run within cmdline backend"
    )


@pytest.fixture(scope="module")
def infrastructure(
    request,
    backend,
    message_bus,
    controller_modules,
    extra_module_paths,
    cmdline_script_root,
    env_overrides,
):
    if message_bus == "mqtt":
        infrastructure_class = MqttInfrastructure
    elif message_bus == "ubus":
        infrastructure_class = UbusInfrastructure
    elif message_bus == "unix-socket":
        infrastructure_class = UnixSocketInfrastructure
    else:
        raise ValueError(f"Unknown message bus {message_bus}")

    instance = infrastructure_class(
        backend,
        controller_modules,
        extra_module_paths,
        UCI_CONFIG_DIR_PATH,
        cmdline_script_root,
        FILE_ROOT_PATH,
        CLIENT_SOCKET_PATH,
        debug_output=request.config.getoption("--debug-output"),
        env_overrides=env_overrides,
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
    if request.node.get_closest_marker("uci_config_path"):
        dir_path = request.node.get_closest_marker("uci_config_path").args[0]
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
    _override_exception("should return a path to a file root dir which are run within file backend")


@pytest.fixture(autouse=True, scope="function")
def file_root_init(request, file_root):
    if request.node.get_closest_marker("file_root_path"):
        dir_path = request.node.get_closest_marker("file_root_path").args[0]
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
    from .svupdater import lists

    try:
        os.unlink(lists.LISTS_FILE_PATH)
    except Exception:
        pass

    set_package_lists()
    yield lists.LISTS_FILE_PATH

    try:
        os.unlink(lists.LISTS_FILE_PATH)
    except Exception:
        pass


@pytest.fixture(scope="function")
def updater_languages():
    from .svupdater import l10n

    try:
        os.unlink(l10n.LANGS_FILE_PATH)
    except Exception:
        pass

    set_languages()
    yield l10n.LANGS_FILE_PATH

    try:
        os.unlink(l10n.LANGS_FILE_PATH)
    except Exception:
        pass


@pytest.fixture(scope="module")
def notify_cmd(infrastructure):
    def notify(module, action, data, validate=True):
        args = ["foris-notify", "-m", module, "-a", action]
        if infrastructure.name in ["ubus", "unix-socket"]:
            args.extend([infrastructure.name, "--path", infrastructure.notification_sock_path])
        elif infrastructure.name in ["mqtt"]:
            args.extend([infrastructure.name, "--host", MQTT_HOST, "--port", str(MQTT_PORT)])

        args.append(json.dumps(data))

        if not validate:
            args.insert(1, "-n")
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr

    yield notify


@pytest.fixture(scope="module")
def notify_api(extra_module_paths, infrastructure):
    if infrastructure.name == "ubus":
        from foris_controller.buses.ubus import UbusNotificationSender

        sender = UbusNotificationSender(infrastructure.notification_sock_path)

    elif infrastructure.name == "unix-socket":
        from foris_controller.buses.unix_socket import UnixSocketNotificationSender

        sender = UnixSocketNotificationSender(infrastructure.notification_sock_path)

    elif infrastructure.name == "mqtt":
        from foris_controller.buses.mqtt import MqttNotificationSender

        sender = MqttNotificationSender(MQTT_HOST, MQTT_PORT, None)

    def notify(module, action, notification=None, validate=True):
        from foris_controller.utils import get_validator_dirs
        from foris_schema import ForisValidator

        if validate:
            validator = ForisValidator(*get_validator_dirs([module], extra_module_paths))
        else:
            validator = None
        sender.notify(module, action, notification, validator)

    yield notify
    sender.disconnect()


CALLED_COMMAND_TEMPLATE = """\
#!/bin/sh
echo $@ >> %(path)s
exit 0
"""


@pytest.fixture(scope="function")
def sh_command(cmdline_script_root):
    content = CALLED_COMMAND_TEMPLATE % dict(path=SH_CALLED_FILE)
    with FileFaker(cmdline_script_root, "/bin/sh", True, textwrap.dedent(content)):
        yield SH_CALLED_FILE
    try:
        os.unlink(SH_CALLED_FILE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def reboot_command(cmdline_script_root):
    content = CALLED_COMMAND_TEMPLATE % dict(path=REBOOT_CALLED_FILE)
    with FileFaker(cmdline_script_root, "/usr/bin/maintain-reboot", True, textwrap.dedent(content)):
        yield REBOOT_CALLED_FILE
    try:
        os.unlink(REBOOT_CALLED_FILE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def network_restart_command(cmdline_script_root):
    content = CALLED_COMMAND_TEMPLATE % dict(path=NETWORK_RESTART_CALLED_FILE)
    with FileFaker(
        cmdline_script_root, "/usr/bin/maintain-network-restart", True, textwrap.dedent(content)
    ):
        yield NETWORK_RESTART_CALLED_FILE
    try:
        os.unlink(NETWORK_RESTART_CALLED_FILE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def lighttpd_restart_command(cmdline_script_root):
    content = CALLED_COMMAND_TEMPLATE % dict(path=LIGHTTPD_RESTART_CALLED_FILE)
    with FileFaker(
        cmdline_script_root, "/usr/bin/maintain-lighttpd-restart", True, textwrap.dedent(content)
    ):
        yield LIGHTTPD_RESTART_CALLED_FILE
    try:
        os.unlink(LIGHTTPD_RESTART_CALLED_FILE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def device(request):
    DEV_MAP = {"mox": "CZ.NIC Turris Mox Board", "omnia": "Turris Omnia", "turris": "Turris 1.1"}

    device_str = DEV_MAP.get(request.param, "unknown")
    with FileFaker(FILE_ROOT_PATH, "/tmp/sysinfo/model", False, device_str + "\n"):
        yield request.param


@pytest.fixture(scope="function")
def turris_os_version(request):
    with FileFaker(FILE_ROOT_PATH, "/etc/turris-version", False, "%s\n" % request.param):
        yield request.param
