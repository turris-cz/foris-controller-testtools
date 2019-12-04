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


import itertools
import json
import os
import socket
import sys
import time
import re
import subprocess
import struct
import uuid


from paho.mqtt import client as mqtt
from multiprocessing import Process, Value, Lock

from .utils import TURRISHW_ROOT

if sys.version_info < (3, 0):
    import SocketServer
else:
    import socketserver

    SocketServer = socketserver


SOCK_PATH = "/tmp/foris-controller-test.soc"
UBUS_PATH = "/tmp/ubus-foris-controller-test.soc"
NOTIFICATION_SOCK_PATH = "/tmp/foris-controller-notifications-test.soc"
NOTIFICATIONS_OUTPUT_PATH = "/tmp/foris-controller-notifications-test.json"
MQTT_HOST = "localhost"
MQTT_PORT = 11883
MQTT_ID = os.environ.get("TEST_CLIENT_ID", f"{uuid.getnode():016X}")

notifications_lock = Lock()


def _wait_for_ubus_module(module, socket_path, timeout=2):
    import ubus

    wait_process = subprocess.Popen(
        ["ubus", "-t", str(timeout), "wait_for", module, "-s", socket_path]
    )
    wait_process.wait()


class ClientSocket(object):
    def __init__(self, socket_path, message_bus=None):
        self.socket_path = socket_path
        self.socket = None
        self.message_bus = message_bus

    def connect(self):
        while not os.path.exists(self.socket_path):
            time.sleep(0.3)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)

    def close(self):
        if self.socket:
            self.socket.close()
        self.socket = None

    def request(self, msg, timeout=3):
        if not self.socket:
            self.connect()

        if self.message_bus == "ubus":
            _wait_for_ubus_module("foris-controller-%s" % msg.get("module", "?"), UBUS_PATH)

        self.socket.settimeout(timeout)

        data = json.dumps(msg).encode("utf8")
        length_bytes = struct.pack("I", len(data))
        self.socket.sendall(length_bytes + data)

        length = struct.unpack("I", self.socket.recv(4))[0]
        received = self.socket.recv(length)
        recv_len = len(received)
        while recv_len < length:
            received += self.socket.recv(length)
            recv_len = len(received)

        return json.loads(received.decode("utf8"))

    def notification(self, msg):
        if not self.socket:
            self.connect()

        data = json.dumps(msg).encode("utf8")
        length_bytes = struct.pack("I", len(data))
        self.socket.sendall(length_bytes + data)


class Infrastructure(object):
    def __init__(
        self,
        name,
        backend_name,
        modules,
        extra_module_paths,
        uci_config_dir,
        cmdline_script_root,
        file_root,
        client_socket_path=None,
        debug_output=False,
        env_overrides={},
    ):
        self.client_socket_path = client_socket_path
        self.client_socket = ClientSocket(client_socket_path, name) if client_socket_path else None
        try:
            os.unlink(SOCK_PATH)
        except Exception:
            pass
        if client_socket_path:
            try:
                os.unlink(client_socket_path)
            except Exception:
                pass

        self.name = name
        self.backend_name = backend_name
        if name not in ["unix-socket", "ubus", "mqtt"]:
            raise NotImplementedError()
        if backend_name not in ["openwrt", "mock"]:
            raise NotImplementedError()

        self.sock_path = SOCK_PATH
        if name == "ubus":
            self.sock_path = UBUS_PATH
            while not os.path.exists(self.sock_path):
                time.sleep(0.3)

        new_env = dict(os.environ)
        new_env["DEFAULT_UCI_CONFIG_DIR"] = uci_config_dir
        new_env["FORIS_CMDLINE_ROOT"] = cmdline_script_root
        new_env["FORIS_FILE_ROOT"] = file_root
        new_env["TURRISHW_ROOT"] = TURRISHW_ROOT
        new_env["FC_UPDATER_MODULE"] = "foris_controller_testtools.svupdater"

        new_env.update(env_overrides)

        kwargs = {"env": new_env}
        if not debug_output:
            devnull = open(os.devnull, "wb")
            kwargs["stderr"] = devnull
            kwargs["stdout"] = devnull

        self._exiting = Value("i", 0)
        self._exiting.value = False

        if name == "unix-socket":
            self.listener = Process(target=unix_notification_listener, args=tuple())
            self.listener.start()
        elif name == "ubus":
            self.listener = Process(target=ubus_notification_listener, args=(self._exiting,))
            self.listener.start()
        elif name == "mqtt":
            self.listener = Process(target=mqtt_notification_listener, args=(MQTT_HOST, MQTT_PORT))
            self.listener.start()

        modules = list(itertools.chain.from_iterable([("-m", e) for e in modules]))
        extra_paths = list(
            itertools.chain.from_iterable([("--extra-module-path", e) for e in extra_module_paths])
        )

        client_socket_option = ["-C", client_socket_path] if client_socket_path else []
        args = (
            ["foris-controller"]
            + modules
            + extra_paths
            + client_socket_option
            + ["-d", "-b", backend_name, name]
        )

        if name == "unix-socket":
            args.append("--path")
            args.append(self.sock_path)
            args.append("--notifications-path")
            args.append(NOTIFICATION_SOCK_PATH)
            self.notification_sock_path = NOTIFICATION_SOCK_PATH
        elif name == "ubus":
            args.append("--path")
            args.append(self.sock_path)
            self.notification_sock_path = self.sock_path
        elif name == "mqtt":
            args.append("--host")
            args.append(MQTT_HOST)
            args.append("--port")
            args.append(str(MQTT_PORT))
            self.notification_host = MQTT_HOST
            self.notification_port = MQTT_PORT

        self.server = subprocess.Popen(args, **kwargs)
        self.connected = False

    def exit(self):
        self._exiting.value = True
        self.server.kill()
        self.listener.terminate()
        self.client_socket.close()
        for path in [NOTIFICATIONS_OUTPUT_PATH, self.client_socket_path]:
            try:
                os.unlink(path)
            except OSError:
                pass
        try:
            import ubus  # disconnect from ubus if connected

            ubus.disconnect()
        except Exception:
            pass

    @staticmethod
    def chunks(data, size):
        for i in range(0, len(data), size):
            yield data[i : i + size]

    def wait_mqtt_connected(self):
        if not self.connected:

            def on_connect(client, userdata, flags, rc):
                client.subscribe(f"foris-controller/{MQTT_ID}/notification/remote/action/advertize")

            def on_message(client, userdata, msg):
                try:
                    if json.loads(msg.payload)["data"]["state"] in ["started", "running"]:
                        client.loop_stop(True)
                except Exception:
                    pass

            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            while True:
                try:
                    client.connect(MQTT_HOST, MQTT_PORT, 30)
                    break
                except ConnectionError:
                    time.sleep(0.1)  # Socket may not be created yet
            client.loop_start()
            client._thread.join(10)
            client.disconnect()
            self.connected = True

    def process_message(self, data):
        if self.name == "unix-socket":
            while not os.path.exists(self.sock_path):
                time.sleep(1)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.sock_path)
            data = json.dumps(data).encode("utf8")
            length_bytes = struct.pack("I", len(data))
            sock.sendall(length_bytes + data)

            length = struct.unpack("I", sock.recv(4))[0]
            received = sock.recv(length)
            recv_len = len(received)
            while recv_len < length:
                received += sock.recv(length)
                recv_len = len(received)

            return json.loads(received.decode("utf8"))

        elif self.name == "ubus":
            import ubus

            if not ubus.get_connected():
                ubus.connect(self.sock_path)
            module = "foris-controller-%s" % data.get("module", "?")
            _wait_for_ubus_module(module, self.sock_path)
            function = data.get("action", "?")
            inner_data = data.get("data", None)
            dumped_data = json.dumps(inner_data)
            request_id = str(uuid.uuid4())
            if len(dumped_data) > 512 * 1024:
                for data_part in Infrastructure.chunks(dumped_data, 512 * 1024):
                    ubus.call(
                        module,
                        function,
                        {
                            "payload": {"multipart_data": data_part},
                            "final": False,
                            "multipart": True,
                            "request_id": request_id,
                        },
                    )

                res = ubus.call(
                    module,
                    function,
                    {
                        "payload": {"multipart_data": ""},
                        "final": True,
                        "multipart": True,
                        "request_id": request_id,
                    },
                )

            else:
                res = ubus.call(
                    module,
                    function,
                    {
                        "payload": {"data": inner_data} if inner_data is not None else {},
                        "final": True,
                        "multipart": False,
                        "request_id": request_id,
                    },
                )

            ubus.disconnect()
            resp = json.loads("".join([e["data"] for e in res]))
            if "errors" in resp:
                return {
                    "module": data["module"],
                    "action": data["action"],
                    "kind": "reply",
                    "errors": resp["errors"],
                }
            if "data" in resp:
                return {
                    "module": data["module"],
                    "action": data["action"],
                    "kind": "reply",
                    "data": resp["data"],
                }
            return {"module": data["module"], "action": data["action"], "kind": "reply"}

        elif self.name == "mqtt":
            self.wait_mqtt_connected()

            output = {}
            msg_id = uuid.uuid1()

            reply_topic = "foris-controller/%s/reply/%s" % (MQTT_ID, msg_id)
            publish_topic = "foris-controller/%s/request/%s/action/%s" % (
                MQTT_ID,
                data["module"],
                data["action"],
            )

            msg = {"reply_msg_id": str(msg_id)}
            if "data" in data:
                msg["data"] = data["data"]

            def on_message(client, userdata, msg):
                output.update(json.loads(msg.payload))
                client.disconnect()
                client.loop_stop(True)

            def on_connect(client, userdata, flags, rc):
                client.subscribe(reply_topic)

            def on_subscribe(client, userdata, mid, granted_qos):
                client.publish(publish_topic, json.dumps(msg))

            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.on_subscribe = on_subscribe
            client.connect(MQTT_HOST, MQTT_PORT, 30)
            client.loop_start()
            client._thread.join(30)
            return output

        else:
            raise NotImplementedError()

    def process_message_ubus_raw(self, data, request_id, final, multipart, multipart_data):
        import ubus

        if not ubus.get_connected():
            ubus.connect(self.sock_path)
        module = "foris-controller-%s" % data.get("module", "?")
        _wait_for_ubus_module(data.get("module", "?"), self.sock_path)
        function = data.get("action", "?")
        payload = {}
        if data is not None:
            payload["data"] = data
        if multipart_data is not None:
            payload["multipart_data"] = multipart_data
        res = ubus.call(
            module,
            function,
            {"payload": payload, "final": final, "multipart": multipart, "request_id": request_id},
        )
        if not res:
            return None
        resp = json.loads("".join([e["data"] for e in res]))
        if "errors" in resp:
            return {
                "module": data["module"],
                "action": data["action"],
                "kind": "reply",
                "errors": resp["errors"],
            }
        if "data" in resp:
            return {
                "module": data["module"],
                "action": data["action"],
                "kind": "reply",
                "data": resp["data"],
            }
        return {"module": data["module"], "action": data["action"], "kind": "reply"}

    def get_notifications(self, old_data=None, filters=[]):
        def filter_data(data):
            if data is None:
                return None
            else:
                return [e for e in data if not filters or (e["module"], e["action"]) in filters]

        while not os.path.exists(NOTIFICATIONS_OUTPUT_PATH):
            time.sleep(0.2)

        global notifications_lock

        while True:
            with notifications_lock, open(NOTIFICATIONS_OUTPUT_PATH) as f:
                data = f.readlines()
                last_data = [json.loads(e.strip()) for e in data]
                filtered_data = filter_data(last_data)
                if not filter_data(old_data) == filtered_data:
                    break
        return filtered_data


def ubus_notification_listener(exiting):
    import prctl
    import signal

    prctl.set_pdeathsig(signal.SIGKILL)
    import ubus

    if ubus.get_connected():
        ubus.disconnect(False)
    ubus.connect(UBUS_PATH)
    global notifications_lock

    try:
        os.unlink(NOTIFICATIONS_OUTPUT_PATH)
    except OSError:
        if os.path.exists(NOTIFICATIONS_OUTPUT_PATH):
            raise

    with open(NOTIFICATIONS_OUTPUT_PATH, "w") as f:
        f.flush()

        def handler(module, data):
            module_name = module[len("foris-controller-") :]
            msg = {"module": module_name, "kind": "notification", "action": data["action"]}
            if "data" in data:
                msg["data"] = data["data"]

            with notifications_lock:
                f.write(json.dumps(msg) + "\n")
                f.flush()

        ubus.listen(("foris-controller-*", handler))
        while True:
            ubus.loop(200)
            if exiting.value:
                break


def mqtt_notification_listener(host, port):
    import prctl
    import signal

    prctl.set_pdeathsig(signal.SIGKILL)
    import ubus

    global notifications_lock

    try:
        os.unlink(NOTIFICATIONS_OUTPUT_PATH)
    except OSError:
        if os.path.exists(NOTIFICATIONS_OUTPUT_PATH):
            raise

    with open(NOTIFICATIONS_OUTPUT_PATH, "w") as f:
        f.flush()

        def on_connect(client, userdata, flags, rc):
            client.subscribe(
                "foris-controller/%s/notification/+/action/+"
                % os.environ.get("TEST_CLIENT_ID", "+")
            )

        def on_message(client, userdata, msg):
            try:
                parsed = json.loads(msg.payload)
            except Exception:
                return

            match = re.match(
                r"^foris-controller/[^/]+/notification/([^/]+)/action/([^/]+)$", msg.topic
            )

            if match:
                module, action = match.group(1, 2)
                msg = {"module": module, "action": action, "kind": "notification"}
                if "data" in parsed:
                    msg["data"] = parsed["data"]
                with notifications_lock:
                    f.write(json.dumps(msg) + "\n")
                    f.flush()

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(host, port)
        client.loop_forever()


def unix_notification_listener():
    import prctl
    import signal
    from threading import Lock

    lock = Lock()
    prctl.set_pdeathsig(signal.SIGKILL)
    global notifications_lock

    try:
        os.unlink(NOTIFICATION_SOCK_PATH)
    except OSError:
        if os.path.exists(NOTIFICATION_SOCK_PATH):
            raise
    try:
        os.unlink(NOTIFICATIONS_OUTPUT_PATH)
    except OSError:
        if os.path.exists(NOTIFICATIONS_OUTPUT_PATH):
            raise

    class Server(SocketServer.ThreadingMixIn, SocketServer.UnixStreamServer):
        pass

    with open(NOTIFICATIONS_OUTPUT_PATH, "wb") as f:
        f.flush()

        class Handler(SocketServer.StreamRequestHandler):
            def handle(self):
                while True:
                    length_raw = self.rfile.read(4)
                    if len(length_raw) != 4:
                        break
                    length = struct.unpack("I", length_raw)[0]
                    data = self.rfile.read(length)
                    with lock:
                        with notifications_lock:
                            f.write(data + b"\n")
                            f.flush()

        server = Server(NOTIFICATION_SOCK_PATH, Handler)
        server.serve_forever()
