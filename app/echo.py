# Fork of https://gitlab.com/n0r1sk/echo/
# Copyright 2020 VoteAmerica
# Copyright 2017 Rausch Bernhard and Kleinsasser Mario
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import socket
import socketserver
import sys
import threading
from datetime import datetime

from netifaces import AF_INET, ifaddresses, interfaces

hostname = None
ips = None


class myTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"{get_time()} Data received: {str(self.data, 'utf-8')}")
        sys.stdout.flush()
        self.request.sendall(
            bytes(
                "Container information:\nHostname:\t"
                + hostname
                + "\n\n"
                + ips
                + "\nTCP Remote information:\nIP:\t"
                + self.client_address[0]
                + "\n\nData received:\n",
                "utf-8",
            )
            + self.data
            + bytes("\n", "utf-8")
        )


class myUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print(f"{get_time()} Data received: {str(data)}")
        sys.stdout.flush()
        socket.sendto(
            bytes(
                "Container information:\nHostname:\t"
                + hostname
                + "\n\n"
                + ips
                + "\nUDP Remote information:\nIP:\t"
                + self.client_address[0]
                + "\n\nData received:\n",
                "utf-8",
            )
            + data
            + bytes("\n", "utf-8"),
            self.client_address,
        )


class myTCPWrapper(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

    def run(self):
        tcp_s = socketserver.TCPServer((self.host, self.port), myTCPHandler)
        tcp_s.serve_forever()


class myUDPWrapper(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

    def run(self):
        udp_s = socketserver.UDPServer((self.host, self.port), myUDPHandler)
        udp_s.serve_forever()


def ip4_addresses():
    ip_list = "Interface\tNetMask\t\tIP\n"
    for interface in interfaces():
        ip_list = ip_list + interface + "\t\t"
        for link in ifaddresses(interface).get(AF_INET, ()):
            ip_list = ip_list + link["netmask"] + "\t"
            ip_list = ip_list + link["addr"] + "\t"
        ip_list = ip_list + "\n"
    return ip_list


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    host, port = "0.0.0.0", 3333

    hostname = socket.gethostname()

    ips = ip4_addresses()
    print(f"turnout echo container started at {get_time()}")
    sys.stdout.flush()

    t_tcp = myTCPWrapper(host, port)
    t_udp = myUDPWrapper(host, port)

    t_tcp.start()
    t_udp.start()
