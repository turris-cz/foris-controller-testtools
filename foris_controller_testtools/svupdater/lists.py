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

import copy
import json
import typing
from .. import utils

LISTS_FILE_PATH = "/tmp/updater-mock-lists.json"
__PKGLIST_ENTRIES = typing.Dict[
    str, typing.Union[
        str, bool, typing.Dict[str, typing.Union[str, bool]]
    ]
]


def pkglists(lang) -> typing.Dict[str, __PKGLIST_ENTRIES]:
    with open(LISTS_FILE_PATH) as f:
        stored = json.load(f)

    res = {}
    for name, lst in stored.items():
        res[name] = {
            "title": lst["title"].get(lang, lst["title"]["en"]),
            "description": lst["description"].get(lang, lst["description"]["en"]),
            "enabled": lst["enabled"],
            "hidden": lst["hidden"],
            "official": lst.get("official", False),
            "url": lst.get("url", ""),
            "options": {},
        }
        for opt_name, option in lst.get("options", {}).items():
            res[name]["options"][opt_name] = {
                "enabled": option.get("enabled", option.get("default", False)),
                "title": option["title"],
                "description": option["description"],
            }

    return res


def update_pkglists(lists: typing.Dict[str, typing.Dict[str, bool]]):
    res = copy.deepcopy(utils.DEFAULT_USERLISTS)
    for name, options in lists.items():
        res[name]["enabled"] = True
        for opt_name, enabled in options.items():
            res[name]["options"][opt_name]["enabled"] = enabled

    with open(LISTS_FILE_PATH, "w") as f:
        json.dump(res, f)
        f.flush()

    return True
