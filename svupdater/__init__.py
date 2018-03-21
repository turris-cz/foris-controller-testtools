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


import os
import subprocess

from .hook import register

RUNNING_FILE_PATH = "/tmp/updater-running-mock"


def opkg_lock():
    return os.path.exists(RUNNING_FILE_PATH)


def run(hooklist=[]):
    if hooklist:
        register(hooklist[0])

    subprocess.Popen(["python", "-m", "svupdater"])
    return True
