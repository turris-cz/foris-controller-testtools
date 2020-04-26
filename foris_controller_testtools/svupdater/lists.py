# -*- coding: utf-8 -*-

# foris-controller-testtools
# Copyright (C) 2018-2020 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import typing
from .. import utils

LISTS_FILE_PATH = "/tmp/updater-mock-lists.json"
__PKGLIST_ENTRIES_LABELS = typing.Dict[str, str]
__PKGLIST_ENTRIES_OPTIONS = typing.Dict[str, typing.Union[str, bool, __PKGLIST_ENTRIES_LABELS]]
__PKGLIST_ENTRIES = typing.Dict[
    str, typing.Union[
        str, bool, __PKGLIST_ENTRIES_OPTIONS, __PKGLIST_ENTRIES_LABELS, object
    ]
]


def _get_labels(known_labels, labels):
    """Convert list of label names to label dictionaries with all info.
    """
    return {
        lbl: {
            "title": known_labels[lbl]['title'],
            "description": known_labels[lbl]['description'],
            "severity": known_labels[lbl].get('severity', "primary"),
        } for lbl in labels if lbl in known_labels.keys()
    }


def _get_options(pkglist_name, stored, known_labels, options):
    """Convert list of options to option dictionaries with all info.
    """
    return {
        name: {
            "enabled": pkglist_name in stored.keys() or option.get("default", False),
            "title": option['title'],
            "description": option['description'],
            "url": option.get('url'),
            "labels": _get_labels(known_labels, option.get('labels', {})),
        } for name, option in options.items()
    }


def pkglists(lang) -> typing.Dict[str, __PKGLIST_ENTRIES]:
    known_lists = utils.DEFAULT_PACKAGE_LISTS
    known_labels = utils.OPTION_LABELS

    with open(LISTS_FILE_PATH) as f:
        stored = json.load(f)

    return {
        name: {
            "enabled": name in stored,
            "title": lst["title"].get(lang, lst["title"]["en"]),
            "description": lst["description"].get(lang, lst["title"]["en"]),
            "url": lst.get("url"),
            "options": _get_options(name, stored, known_labels, lst.get("options", {})),
            "labels": _get_labels(known_labels, lst.get("labels", {})),
        } for name, lst in known_lists.items()
    }


def update_pkglists(lists: typing.Dict[str, typing.Dict[str, bool]]):
    known_lists = utils.DEFAULT_PACKAGE_LISTS
    res = {}
    for name, options in lists.items():
        res[name] = known_lists[name]
        res[name]["enabled"] = True
        default_list_options = known_lists[name].get("options", {})
        opts = {}
        for opt_name, value in options.items():
            if opt_name in default_list_options:
                opts[opt_name] = default_list_options[opt_name]
                opts[opt_name]["enabled"] = value

        res[name]["options"] = opts

    with open(LISTS_FILE_PATH, "w") as f:
        json.dump(res, f)
        f.flush()

    return True
