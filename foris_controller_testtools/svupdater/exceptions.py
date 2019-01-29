#
# foris-controller-testtools
# Copyright (C) 2019 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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


class ExceptionUpdaterDisabled(Exception):
    """This exception is thrown when you try to run updater when it's
    configured to be disabled.
    """
    pass


class ExceptionUpdaterApproveInvalid(Exception):
    """Exception thrown from either approve.approve() or approve.deny() when
    given hash doesn't match the one from approve.current().
    """
    pass


class ExceptionUpdaterPidLockFailure(Exception):
    """This exception is thrown when we encounter some invalid usage of
    pidlock.
    """
    pass


class ExceptionUpdaterNoSuchList(Exception):
    """Exception thrown from lists.update when non-existent list is given.
    """
    pass


class ExceptionUpdaterNoSuchLang(Exception):
    """Exception thrown from l10n.update when unsupported language code is
    given.
    """
    pass


class ExceptionUpdaterInvalidHookCommand(Exception):
    """Thrown from hook.register when argument command contains more than one
    line.
    """
    pass
