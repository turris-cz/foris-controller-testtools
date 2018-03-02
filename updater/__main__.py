#
# foris-controller
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

import time
import sys
import socket

from foris_controller_testtools.infrastructure import ClientSocket
from foris_controller_testtools.fixtures import CLIENT_SOCKET_PATH, REBOOT_INDICATOR_PATH

if __name__ == "__main__":

    sock = ClientSocket(CLIENT_SOCKET_PATH)

    def send_notication(data):
        sock.notification({
            "module": "updater",
            "kind": "notification",
            "action": "run",
            "data": data,
        })

    try:
        # mock updater run
        send_notication({"status": "initialize"})
        time.sleep(0.2)
        send_notication({"status": "install", "msg": "package1-0.2"})
        time.sleep(0.2)
        send_notication({"status": "exit"})

    except socket.error:
        # server probably disconnected
        pass

    if len(sys.argv) > 1 and "-p" in sys.argv[1:]:
        with open(REBOOT_INDICATOR_PATH, "w") as f:
            f.flush()
