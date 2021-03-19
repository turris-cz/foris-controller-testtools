# -*- coding: utf-8 -*-

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
GENERIC_CALLED_FILE = "/tmp/command_called"
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


def command_was_called(args=[], cleanup=True):
    """ Checks whether a generic command or binary was called
    :param args: arguments of the script
    :param args: iterable
    :param cleanup: remove GENERIC_CALLED_FILE after check
    :param cleanup: bool
    :returns: True if script was called
    """
    return _command_was_called(GENERIC_CALLED_FILE, args, cleanup)


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


DEFAULT_PACKAGE_LISTS = {
    "3g": {
        "title": {
            "en": "Extensions of network protocols for 3G/LTE"
        },
        "description": {
            "en": "Support for Turris Omnia and Turris MOX LTE pack."
        },
        "url": "https://wiki.turris.cz/doc/en/howto/lte_modem_install",
        "enabled": False
    },
    "datacollect": {
        "title": {
            "en": "Data Collection"
        },
        "description": {
            "en": "Software for participation in data collection and distributed adaptive firewall."
        },
        "url": "https://docs.turris.cz/basics/collect/",
        "options": {
            "survey": {
                "title": "Usage Survey",
                "description": "Collect data about router usage (installed packages, Internet connection type and etc.).",
                "default": True
            },
            "dynfw": {
                "title": "Dynamic Firewall",
                "description": "Add firewall rules to block attackers detected by Turris collection network.",
                "default": True
            },
            "nikola": {
                "title": "Firewall Logs",
                "description": "Collect logs from firewall for attempted connections.",
                "default": True
            },
            "minipot": {
                "title": "Minipots",
                "description": "Minimal honeypots to catch attackers for various protocols.",
                "default": True
            },
            "haas": {
                "title": "SSH Honeypot",
                "description": "SSH honeypot using Honeypot as a Service (haas.nic.cz)."
            }
        },
        "enabled": False
    },
    "atlas": {
        "title": {
            "en": "RIPE Atlas SW Probe"
        },
        "description": {
            "en": "Global platform, which measures Internet connectivity and reachability."
        },
        "url": "https://wiki.turris.cz/doc/en/howto/atlas-probe",
        "labels": [
            "community"
        ],
        "enabled": False
    },
    "dvb": {
        "title": {
            "en": "DVB tuner"
        },
        "description": {
            "en": "Software for sharing television received by a DVB tuner on Turris. Does not include device drivers."
        },
        "url": "https://wiki.turris.cz/doc/en/howto/dvb",
        "labels": [
            "community",
            "advanced"
        ],
        "enabled": False
    },
    "hardening": {
        "title": {
            "en": "Hardening"
        },
        "description": {
            "en": "Seccomp tools for system hardening."
        },
        "options": {
            "common_passwords": {
                "title": "Common passwords filter",
                "description": "Compare new password you are about to set to access router with list of common passwords used by robots trapped in Turris honeypots.",
                "default": True
            },
            "ujail": {
                "title": "OpenWrt's process jail",
                "description": "ujail allows to limit processes by limiting syscalls and file-system access",
                "labels": [
                    "community",
                    "experimental"
                ]
            },
            "seccomp": {
                "title": "Secure Computing Mode (seccomp)",
                "description": "Optional support for seccomp allowing processes to isolate from them self",
                "labels": [
                    "community",
                    "experimental"
                ]
            }
        },
        "enabled": False
    },
    "luci_controls": {
        "title": {
            "en": "LuCI extensions"
        },
        "description": {
            "en": "Several additional tabs and controls for the advanced LuCI interface."
        },
        "options": {
            "adblock": {
                "title": "AdBlock",
                "description": "Script to block ad/abuse domains."
            },
            "sqm": {
                "title": "SQM",
                "description": "Active Queue Management to boost performance on heavily loaded network."
            },
            "tinyproxy": {
                "title": "Tinyproxy",
                "description": "HTTP(S) proxy."
            },
            "upnp": {
                "title": "UPnP",
                "description": "Universal Plug and Play service."
            },
            "printserver": {
                "title": "Print server (p910nd)",
                "description": "Services allowing to connect a printer to the router and use it for remote printing."
            },
            "statistics": {
                "title": "Statistics",
                "description": "Gather and render diagrams for system statistics by using collectd."
            },
            "wireguard": {
                "title": "WireGuard",
                "description": "Alternative to OpenVPN, it provides fast, modern and secure VPN tunnel.",
                "url": "https://openwrt.org/docs/guide-user/services/vpn/wireguard/start",
                "labels": [
                    "advanced"
                ]
            }
        },
        "labels": [
            "community"
        ],
        "enabled": False
    },
    "lxc": {
        "title": {
            "en": "LXC utilities"
        },
        "description": {
            "en": "Set of utilities to manage Linux Containers (lightweight virtualization technology)."
        },
        "url": "https://docs.turris.cz/geek/lxc/lxc/",
        "labels": [
            "storage",
            "high_memory",
            "advanced"
        ],
        "enabled": False
    },
    "nas": {
        "title": {
            "en": "NAS"
        },
        "description": {
            "en": "Services allowing to connect a disk to the router and use it as network data store."
        },
        "url": "https://wiki.turris.cz/doc/en/howto/nas",
        "options": {
            "samba": {
                "title": "Samba",
                "description": "Implementation of SMB network protocol."
            },
            "dlna": {
                "title": "DLNA",
                "description": "Digital media sharing server."
            },
            "transmission": {
                "title": "Transmission",
                "description": "BitTorrent client."
            },
            "raid": {
                "title": "mdadm",
                "description": "Software RAID storage support using mdadm.",
                "labels": [
                    "advanced"
                ]
            },
            "encrypt": {
                "title": "Encrypted Storage",
                "description": "Add support to access encrypted storage devices using dm-crypt.",
                "labels": [
                    "advanced"
                ]
            }
        },
        "labels": [
            "community"
        ],
        "enabled": False
    },
    "net_monitoring": {
        "title": {
            "en": "Network monitoring and parental control"
        },
        "description": {
            "en": "Tools to monitor local network and users on it."
        },
        "options": {
            "netmetr": {
                "title": "Internet connection speed measurement",
                "description": "Actively measures speed of Internet connection using netmetr.cz service.",
                "url": "https://docs.turris.cz/basics/apps/netmetr/"
            },
            "dev_detect": {
                "title": "New devices detection",
                "description": "Software for detecting new devices on local network.",
                "labels": [
                    "experimental"
                ]
            },
            "pakon": {
                "title": "Pakon",
                "description": "Software for in depth monitoring of your traffic using Suricata.",
                "url": "https://docs.turris.cz/basics/apps/pakon/",
                "labels": [
                    "experimental",
                    "netload",
                    "high_memory",
                    "storage"
                ]
            }
        },
        "enabled": False
    },
    "netboot": {
        "title": {
            "en": "Turris MOX network boot"
        },
        "description": {
            "en": "Server-side for Turris MOX without microSD card used as Wi-Fi access point."
        },
        "url": "https://docs.turris.cz/basics/apps/netboot",
        "labels": [
            "high_storage",
            "experimental"
        ],
        "enabled": False
    },
    "netdata": {
        "title": {
            "en": "Netdata"
        },
        "description": {
            "en": "Real-time perfomance and health monitoring options."
        },
        "labels": [
            "community",
            "high_memory"
        ],
        "enabled": False
    },
    "nextcloud": {
        "title": {
            "en": "Nextcloud"
        },
        "description": {
            "en": "Self-hosted files hosting and productivity platform that keeps you in control. Alternative to services such as Dropbox or Google Drive."
        },
        "url": "https://docs.turris.cz/geek/nextcloud/nextcloud/",
        "labels": [
            "experimental",
            "storage"
        ],
        "enabled": False
    },
    "openvpn": {
        "title": {
            "en": "OpenVPN"
        },
        "description": {
            "en": "Easy setup of the OpenVPN server from Foris."
        },
        "url": "https://docs.turris.cz/basics/apps/openvpn/openvpn/",
        "enabled": False
    },
    "tor": {
        "title": {
            "en": "Tor"
        },
        "description": {
            "en": "Service to increase anonymity on the Internet."
        },
        "labels": [
            "advanced",
            "community"
        ],
        "enabled": False
    },
    "drivers": {
        "title": {
            "en": "Alternative core drivers"
        },
        "description": {
            "en": "These options allow you to use alternative drivers over those available in default installation. You can try to enable these if you encounter some problems with default ones."
        },
        "options": {
            "ath10k_ct": {
                "title": "Candela Technologies Wi-Fi drivers for Qualcomm Atheros QCA988x",
                "description": "Alternative driver from Candela Technologies.",
                "boards": [
                    "omnia",
                    "turris1x"
                ]
            },
            "ath10k_ct_htt": {
                "title": "Candela Technologies Wi-Fi drivers for Qualcomm Atheros QCA988x with improved stability in busy networks",
                "description": "Alternative driver from Candela Technologies. It uses HTT TX data path for management frames, which improves stability in busy networks."
            }
        },
        "labels": [
            "advanced",
            "community"
        ],
        "enabled": False
    }
}

OPTION_LABELS = {
        "advanced": {
            "title": "Advanced users",
            "description": "This functionality is usable only for advanced users.",
            "severity": "secondary"
        },
        "community": {
            "title": "Community",
            "description": "This package list is not officially supported. Turris team has no responsibility for stability of software that is part of this list.",
            "severity": "success"
        },
        "experimental": {
            "title": "Experimental",
            "description": "Software that is part of this package list is considered experimental. Problems when using it can be expected.",
            "severity": "danger"
        },
        "deprecated": {
            "title": "Deprecated",
            "description": "This package list and/or software that provides are planned to be removed. It is advised to not use it.",
            "severity": "warning"
        },
        "storage": {
            "title": "External storage",
            "description": "External storage use is highly suggested for use of this package list",
            "severity": "primary"
        },
        "high_memory": {
            "title": "High memory usage",
            "description": "Software in this package list consumes possibly higher amount of memory to run. It is not suggested to use it with small memory.",
            "severity": "info"
        },
        "high_storage": {
            "title": "High storage usage",
            "description": "Software in this package list consumes possibly higher amount of storage space to install. It is not suggested to use it with small storages such as internal storage of Turris 1.x and SD cards with less than 1GB of storage.",
            "severity": "info"
        },
        "netload": {
            "title": "Network load",
            "description": "This functionality can decreases network performance. That can be felt only on faster uplinks but because of that it still can be decremental to some users.",
            "severity": "secondary"
        }
    }


def set_package_lists(lists=None):
    """ Sets mocked package lists
    :param lists: {"nas": {...}, "api-token": {...}, ...}
    :type lists: dict
    """
    if not lists:
        lists = DEFAULT_PACKAGE_LISTS

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
