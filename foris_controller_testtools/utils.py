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
import updater

INIT_SCRIPT_TEST_DIR = "/tmp/test_init"
SH_CALLED_FILE = "/tmp/sh_called"


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
            os.unlink(updater.APPROVAL_FILE_PATH)
        except Exception:
            pass
    else:
        with open(updater.APPROVAL_FILE_PATH, "w") as f:
            json.dump(approval, f)
            f.flush()
