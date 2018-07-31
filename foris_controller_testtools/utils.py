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

import json
import os
import stat
import svupdater
import svupdater.lists
import svupdater.l10n
import svupdater.approvals

INIT_SCRIPT_TEST_DIR = "/tmp/test_init"
SH_CALLED_FILE = "/tmp/sh_called"


def get_uci_module(lock_backend):
    from foris_controller.app import app_info
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


def check_service_result(name, passed, action):
    path = os.path.join(INIT_SCRIPT_TEST_DIR, name)
    with open(path) as f:
        obtained_passed, obtained_action = f.read().strip().split(" ")
    expected_passed = "passed" if passed else "failed"
    assert obtained_passed == expected_passed
    assert action == obtained_action
    os.unlink(path)


def sh_was_called(script, args=[], cleanup=True):
    """ Checks whether a script was called using sh command
        The sh command should mock shell execution and print its content into SH_CALLED_FILE
    :param script: script which is checked whether it was called
    :param script: str
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove SH_CALLED_FILE after check
    :param cleanup: bool
    :returns: True if script was called
    """

    res = False
    try:
        with open(SH_CALLED_FILE) as f:
            lines = f.readlines()

        script_and_args = " ".join([script] + args)
        for line in lines:
            if script_and_args in line:
                res = True
    except Exception:
        pass

    if cleanup:
        try:
            os.unlink(SH_CALLED_FILE)
        except Exception:
            pass

    return res


def set_approval(approval=None):
    """ Sets mocked approval
    :param approval: new approval (or removes approval if None)
    :type approval: None or dict
    """
    if approval is None:
        try:
            os.unlink(svupdater.approvals.APPROVAL_FILE_PATH)
        except Exception:
            pass
    else:
        with open(svupdater.approvals.APPROVAL_FILE_PATH, "w") as f:
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
    with open(svupdater.l10n.LANGS_FILE_PATH, "w") as f:
        json.dump(langs, f)
        f.flush()


DEFAULT_USERLISTS = {
    "api-token": {
        "message": {
            "en": u"A Foris plugin allowing to manage remote API access tokens"
            " (for example for use in Spectator or Android application).",
            "cs": "Správa tokenů pro vzdálený API přístup"
            " (např. pro Spectator, nebo Android aplikaci) ve Forisu.",
            "de": "Ein Plugin für Foris, welcher Management von Tokens für das"
            " Fernzugriff-API (z. B. für Anwendung in Spectator oder Android"
            " Applikationen) erlaubt.",
        },
        "title": {
            "en": "Access tokens",
            "cs": "Přístupové tokeny",
            "de": "Zugangsverwaltung",
        },
        "enabled": False,
        "hidden": False,
    },
    "automation": {
        "message": {
            "cs": 'Software pro ovládání domácí automatizace, včetně Turris Gadgets.',
            "de": 'Steuerungssoftware für die Hausautomation, einschließlich Turris '
            'Gadgets.',
            "en": 'Control software for home automation, including Turris Gadgets.',

        },
        "title": {
            "cs": 'Domácí automatizace',
            "de": 'Hausautomation',
            "en": 'Home automation',
        },
        "enabled": False,
        "hidden": False,
    },
    "dev-detect": {
        "message": {
            'cs': 'Software pro detekci nově připojených zařízení na lokální síti'
            ' (EXPERIMENTÁLNÍ).',
            'de': 'Software für die Erkennung neuer Geräte im lokalen Netzwerk (EXPERIMENTELL).',
            'en': 'Software for detecting new devices on local network (EXPERIMENTAL).',

        },
        "title": {
            'cs': 'Detekce připojených zařízení',
            'de': 'Geräterkennung',
            'en': 'Device detection',

        },
        "enabled": False,
        "hidden": False,
    },
    "dvb": {
        "message": {
            'cs': 'Software na sdílení televizního vysílání přijímaného Turrisem.'
            ' Neobsahuje ovladače pro zařízení.',
            'de': 'Software für die Weiterleitung von Fernsehsignal, welcher mittels'
            ' DVB-Tuner vom Turris empfangen wird. Gerätetreiber sind nicht enthalten.',
            'en': 'Software for sharing television received by a DVB tuner on Turris.' 
            ' Does not include device drivers.'
        },
        "title": {
            'cs': 'Televizní tuner',
            'de': 'DVB-Tuner',
            'en': 'DVB tuner',

        },
        "enabled": False,
        "hidden": False,
    },
    'i_agree_honeypot': {
        "message": {
            "cs": 'Past na roboty zkoušející hesla na SSH.',
            "de": 'Falle für Roboter, die das Kennwort für den SSH-Zugriff zu erraten versuchen.',
            "en": 'Trap for password-guessing robots on SSH.',

        },
        "title": {
            "cs": 'SSH Honeypot',
            "de": 'SSH-Honigtopf',
            "en": 'SSH Honeypot',
        },
        "enabled": False,
        "hidden": False,
    },
    'i_agree_datacollect': {
        "message": {
            "cs": None,
            "de": None,
            "en": None,
        },
        "title": {
            "cs": None,
            "de": None,
            "en": None,
        },
        "enabled": False,
        "hidden": True,
    },
}


def set_userlists(lists=None):
    """ Sets mocked userlists
    :param lists: {"nas": {...}, "api-token": {...}, ...}
    :type lists: dict
    """
    if not lists:
        lists = DEFAULT_USERLISTS

    with open(svupdater.lists.LISTS_FILE_PATH, "w") as f:
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
