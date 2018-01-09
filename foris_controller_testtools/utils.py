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

import os

INIT_SCRIPT_TEST_DIR = "/tmp/test_init"


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
