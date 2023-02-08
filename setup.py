#!/usr/bin/env python
#
# Copyright (C) 2018-2023 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

from setuptools import setup

from foris_controller_testtools import __version__

DESCRIPTION = """
An program which is placed in top of a message bus and translates requests to commands for backends.
"""

setup(
    name="foris-controller-testtools",
    version=__version__,
    author="CZ.NIC, z.s.p.o. (http://www.nic.cz/)",
    author_email="packaging@turris.cz",
    packages=[
        "foris_controller_testtools",
        "foris_controller_testtools.svupdater",  # mocked updater module
    ],
    url="https://gitlab.nic.cz/turris/foris-controller/foris-controller-testtools",
    license="COPYING",
    description=DESCRIPTION,
    long_description=open("README.rst").read(),
    entry_points={
        "pytest11": ["foris_controller_testtools = foris_controller_testtools.pytest_plugin"]
    },
    package_data={"foris_controller_testtools": ["turrishw/*.tar.gz"]},
    install_requires=[
        "pytest",
        "foris-controller @ git+https://gitlab.nic.cz/turris/foris-controller/foris-controller.git"
    ],
    zip_safe=False,
)
