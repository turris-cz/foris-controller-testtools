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
import json

APPROVAL_FILE_PATH = "/tmp/updater-approval-mock.json"


def current():
    if not os.path.exists(APPROVAL_FILE_PATH):
        return None
    with open(APPROVAL_FILE_PATH) as f:
        return json.load(f)


def approve(approval_hash):
    return _resolve_approval(approval_hash, True)


def deny(approval_hash):
    return _resolve_approval(approval_hash, False)


def _resolve_approval(approval_hash, grant):
    """ resolve approval

    :param approval_hash: id of the approval
    :type approval_hash: string
    :param grant: shall the approval be granted otherwise it will be denied
    :type grant: bool
    """
    # try to find approval
    try:
        with open(APPROVAL_FILE_PATH) as f:
            data = json.load(f)
    except Exception:
        return False

    # check and update status
    if data["hash"] != approval_hash or data["status"] != "asked":
        return False
    data["status"] = "granted" if grant else "denied"

    # write it back
    try:
        with open(APPROVAL_FILE_PATH, "w") as f:
            data = json.dump(data, f)
            f.flush()
    except Exception:
        return False

    return True
