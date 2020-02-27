# -*- coding: utf-8 -*-

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

import time
import json
import os
import shutil
import stat
import tarfile
import multiprocessing
import threading

from .svupdater import lists as svupdater_lists
from .svupdater import l10n as svupdater_l10n
from .svupdater import approvals as svupdater_approvals


INIT_SCRIPT_TEST_DIR = "/tmp/test_init"
SH_CALLED_FILE = "/tmp/sh_called"
REBOOT_CALLED_FILE = "/tmp/reboot_called"
NETWORK_RESTART_CALLED_FILE = "/tmp/network_restart_called"
LIGHTTPD_RESTART_CALLED_FILE = "/tmp/lighttpd_restart_called"
TURRISHW_ROOT = "/tmp/turrishw_root/"


def get_uci_module(lock_backend):
    from foris_controller.app import app_info

    if isinstance(lock_backend, str):
        lock_backend = multiprocessing if lock_backend == "ubus" else threading

    app_info["lock_backend"] = lock_backend
    from foris_controller_backends import uci

    return uci


def match_subdict(expected_data, obtained_data):
    """ Decides whether one dict contains values specified in the second dict
        The second dict may contain extra fields.
        Note that this function is recursive and you need to avoid circular dict

        :param expected_data: data which are expected
        :type expected_data: dict
        :param obtained_data: data which will be examined
        :type expected_data: dict
        :returns: True if matches False otherwise
        :rtype: bool
    """
    for key in expected_data:
        if key not in obtained_data:
            return False
        if isinstance(expected_data[key], dict):
            if not isinstance(obtained_data[key], dict):
                return False
            if not match_subdict(expected_data[key], obtained_data[key]):
                return False
            continue
        if not expected_data[key] == obtained_data[key]:
            return False

    return True


def check_service_result(name, action, passed=None, clean=True, expected_found=True):
    path = os.path.join(INIT_SCRIPT_TEST_DIR, name)
    try:
        with open(path) as f:
            lines = f.readlines()
    except IOError:
        lines = []

    if passed is not None:
        expected_passed = "passed" if passed else "failed"
    else:
        expected_passed = None

    found = False
    for line in lines:
        obtained_passed, obtained_action = line.strip().split(" ")
        if (
            expected_passed is None or obtained_passed == expected_passed
        ) and action == obtained_action:
            found = True

    if clean:
        if os.path.exists(path):
            os.unlink(path)

    assert found is expected_found


def _command_was_called(called_file, args, cleanup):
    res = False
    try:
        with open(called_file) as f:
            lines = f.readlines()

        script_and_args = " ".join(args)
        for line in lines:
            if script_and_args in line:
                res = True
    except Exception:
        pass

    if cleanup:
        try:
            os.unlink(called_file)
        except Exception:
            pass

    return res


def _delay_till_file_exists(path, step=0.1, count=10):
    for _ in range(count):
        if os.path.exists(path):
            break
        time.sleep(step)


def sh_was_called(args=[], cleanup=True):
    """ Checks whether a script was called using sh command
        The sh command should mock shell execution and print its content into SH_CALLED_FILE
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove SH_CALLED_FILE after check
    :param cleanup: bool
    :returns: True if script was called
    """
    return _command_was_called(SH_CALLED_FILE, args, cleanup)


def reboot_was_called(args=[], cleanup=True):
    """ Checks whether a reboot script was called
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove called file after check
    :param cleanup: bool
    :returns: True if script was called
    """
    _delay_till_file_exists(REBOOT_CALLED_FILE)
    return _command_was_called(REBOOT_CALLED_FILE, args, cleanup)


def network_restart_was_called(args=[], cleanup=True):
    """ Checks whether a network restart script was called
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove called file after check
    :param cleanup: bool
    :returns: True if script was called
    """
    _delay_till_file_exists(NETWORK_RESTART_CALLED_FILE)
    return _command_was_called(NETWORK_RESTART_CALLED_FILE, args, cleanup)


def lighttpd_restart_was_called(args=[], cleanup=True):
    """ Checks whether a lighttpd restart script was called
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove called file after check
    :param cleanup: bool
    :returns: True if script was called
    """
    _delay_till_file_exists(LIGHTTPD_RESTART_CALLED_FILE)
    return _command_was_called(LIGHTTPD_RESTART_CALLED_FILE, args, cleanup)


def set_approval(approval=None):
    """ Sets mocked approval
    :param approval: new approval (or removes approval if None)
    :type approval: None or dict
    """
    if approval is None:
        try:
            os.unlink(svupdater_approvals.APPROVAL_FILE_PATH)
        except Exception:
            pass
    else:
        with open(svupdater_approvals.APPROVAL_FILE_PATH, "w") as f:
            json.dump(approval, f)
            f.flush()


DEFAULT_LANGS = {
    "cs": True,
    "de": True,
    "da": False,
    "fr": False,
    "lt": False,
    "pl": False,
    "ru": False,
    "sk": False,
    "hu": False,
    "it": False,
    "nb_NO": True,
}


def set_languages(langs=None):
    """ Sets mocked languages
    :param langs: {"cs": True, "de": True, ...}
    :type langs: dict
    """
    if not langs:
        langs = DEFAULT_LANGS
    with open(svupdater_l10n.LANGS_FILE_PATH, "w") as f:
        json.dump(langs, f)
        f.flush()


DEFAULT_USERLISTS = {
    "api-token": {
        "description": {
            "en": u"A Foris plugin allowing to manage remote API access tokens"
            " (for example for use in Spectator or Android application).",
            "cs": "Správa tokenů pro vzdálený API přístup"
            " (např. pro Spectator, nebo Android aplikaci) ve Forisu.",
            "de": "Ein Plugin für Foris, welcher Management von Tokens für das"
            " Fernzugriff-API (z. B. für Anwendung in Spectator oder Android"
            " Applikationen) erlaubt.",
        },
        "title": {"en": "Access tokens", "cs": "Přístupové tokeny", "de": "Zugangsverwaltung"},
        "enabled": False,
        "hidden": False,
        "official": True,
    },
    "automation": {
        "description": {
            "cs": "Software pro ovládání domácí automatizace, včetně Turris Gadgets.",
            "de": "Steuerungssoftware für die Hausautomation, einschließlich Turris " "Gadgets.",
            "en": "Control software for home automation, including Turris Gadgets.",
        },
        "title": {"cs": "Domácí automatizace", "de": "Hausautomation", "en": "Home automation"},
        "enabled": False,
        "hidden": False,
    },
    "dev-detect": {
        "description": {
            "cs": "Software pro detekci nově připojených zařízení na lokální síti"
            " (EXPERIMENTÁLNÍ).",
            "de": "Software für die Erkennung neuer Geräte im lokalen Netzwerk (EXPERIMENTELL).",
            "en": "Software for detecting new devices on local network (EXPERIMENTAL).",
        },
        "title": {
            "cs": "Detekce připojených zařízení",
            "de": "Geräterkennung",
            "en": "Device detection",
        },
        "enabled": False,
        "hidden": False,
    },
    "dvb": {
        "description": {
            "cs": "Software na sdílení televizního vysílání přijímaného Turrisem."
            " Neobsahuje ovladače pro zařízení.",
            "de": "Software für die Weiterleitung von Fernsehsignal, welcher mittels"
            " DVB-Tuner vom Turris empfangen wird. Gerätetreiber sind nicht enthalten.",
            "en": "Software for sharing television received by a DVB tuner on Turris."
            " Does not include device drivers.",
        },
        "title": {"cs": "Televizní tuner", "de": "DVB-Tuner", "en": "DVB tuner"},
        "enabled": False,
        "hidden": False,
        "url": "https://doc.turris.cz/doc/en/howto/dvb",
    },
    "i_agree_honeypot": {
        "description": {
            "cs": "Past na roboty zkoušející hesla na SSH.",
            "de": "Falle für Roboter, die das Kennwort für den SSH-Zugriff zu erraten versuchen.",
            "en": "Trap for password-guessing robots on SSH.",
        },
        "title": {"cs": "SSH Honeypot", "de": "SSH-Honigtopf", "en": "SSH Honeypot"},
        "enabled": False,
        "hidden": False,
        "official": True,
        "options": {
            "minipot": {
                "title": "Minipots",
                "description": "Minimal honeypots to catch attackers for various protocols.",
                "default": True,
            },
            "haas": {
                "title": "SSH Honeypot",
                "description": "SSH honeypot using Honeypot as a Service (haas.nic.cz)."
            }
        }
    },
    "i_agree_datacollect": {
        "description": {"cs": "", "de": "", "en": ""},
        "title": {"cs": "", "de": "", "en": ""},
        "enabled": False,
        "hidden": True,
        "official": True,
        "options": {
            "survey": {
                "title": "Usage Survey",
                "description": "Collect data about router usage (installed packages, Internet connection type and etc.).",
            },
            "dynfw": {
                "title": "Dynamic Firewall",
                "description": "Add firewall rules to block attackers detected by Turris collection network.",
                "default": True,
            }
        },
    },
}


def set_userlists(lists=None):
    """ Sets mocked userlists
    :param lists: {"nas": {...}, "api-token": {...}, ...}
    :type lists: dict
    """
    if not lists:
        lists = DEFAULT_USERLISTS

    with open(svupdater_lists.LISTS_FILE_PATH, "w") as f:
        json.dump(lists, f)
        f.flush()


class FileFaker(object):
    def __init__(self, path_prefix, path, executable, content):
        """ Intializes fake file
        :param path_prefix: prefixed path (e.g. /path/to/my/custom/root)
        :type path_prefix: str
        :param path: actual file path (e.g. /usr/bin/iw)
        :type path: str
        :param executable: should the file be executable
        :type executable: bool
        :param content: the initial content of the file
        :type content: str
        """
        self.target_path = os.path.join(path_prefix, path.lstrip("/"))
        self.executable = executable
        self.content = content

    def store_file(self):
        """ Stores into file system and updates permissions for the fake file
        """
        try:
            os.makedirs(os.path.dirname(self.target_path))
        except os.error:
            pass  # path might already exist

        self.update_content(self.content)

        if self.executable:
            os.chmod(self.target_path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR)

    def get_content(self):
        """ Reads the current content of the file
            Might be useful is the file is expected to change
        """
        with open(self.target_path) as f:
            return f.read()

    def update_content(self, new_content):
        """ Updates the current content of the file
        """
        with open(self.target_path, "w") as f:
            f.write(new_content)

    def cleanup(self):
        """ Removes targeted file
        """
        if os.path.exists(self.target_path):
            os.unlink(self.target_path)

    def __enter__(self):
        self.store_file()

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


def prepare_turrishw_root(device, version):
    if device == "omnia":
        if version.split(".", 1)[0] == "3":
            prepare_turrishw("omnia-3.X")
        else:
            prepare_turrishw("omnia-4.0")
    elif device == "turris":
        if version.split(".", 1)[0] == "3":
            prepare_turrishw("turris-3.X")
        else:
            prepare_turrishw("turris-4.0")
    elif device == "mox":
        prepare_turrishw("mox+EEC")


def prepare_turrishw(root):
    try:
        shutil.rmtree(TURRISHW_ROOT, ignore_errors=True)
    except Exception:
        pass
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "turrishw", "%s.tar.gz" % root)
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(TURRISHW_ROOT)
