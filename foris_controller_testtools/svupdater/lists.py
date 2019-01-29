# -*- coding: utf-8 -*-

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

LISTS_FILE_PATH = "/tmp/updater-mock-lists.json"


def pkglists(lang):
    with open(LISTS_FILE_PATH) as f:
        data = json.load(f)

    res = {}
    for name, stored in data.items():
        res[name] = {
            "title": stored["title"].get(lang, stored["title"]["en"]),
            "message": stored["message"].get(lang, stored["message"]["en"]),
            "enabled": stored["enabled"],
            "hidden": stored["hidden"],
        }

    return res


def update_pkglists(lists):
    with open(LISTS_FILE_PATH) as f:
        data = json.load(f)
    for name in data.keys():
        data[name]["enabled"] = name in lists

    with open(LISTS_FILE_PATH, "w") as f:
        json.dump(data, f)
        f.flush()

    return True
