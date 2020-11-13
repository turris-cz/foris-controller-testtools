#
# foris-controller-testtools
# Copyright (C) 2020 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
from pathlib import Path
from ..utils import TURRISHW_ROOT


class Status:
    PACKAGES = ["turris-version", "foo-alternative"]
    PROVIDES = {
        "foo-alternative": "foo"
    }

    CUSTOM_FILE_PATH = Path(TURRISHW_ROOT) / "usr/lib/opkg/status.json"

    @classmethod
    def installed(cls, package):
        ret = []

        packages, provides = cls._load_packages()

        if package in packages:
            ret.append(package)

        for name, provides in provides.items():
            if package == provides:
                ret.append(name)

        return tuple(ret)

    @classmethod
    def _load_packages(cls):
        if cls.CUSTOM_FILE_PATH.is_file():
            with open(cls.CUSTOM_FILE_PATH, 'r') as f:
                data = json.load(f)

            installed = data["installed"]
            provides = {item["name"]: item["provides"] for item in data["provides"]}

            return installed, provides

        return cls.PACKAGES, cls.PROVIDES
