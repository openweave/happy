#!/usr/bin/env python

#
#    Copyright (c) 2015-2017 Nest Labs, Inc.
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

##
#    @file
#       Implements Ping class that call ping to virtual nodes.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["source"] = None
options["destination"] = None
options["size"] = None
options["count"] = None


def option():
    return options.copy()


class Ping(HappyNode):
    """
    Sends pings between virtual nodes. Uses ping for IPv4 and ping6 for IPv6.

    happy-ping [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
               [-d --destination (<IP_ADDR>|<NODE_NAME>)]
               [-s --size <PING_SIZE>] [-c --count <PING_COUNT>]

        -i --id           Source node.
        -d --destination  Destination node, can be either the IP address or the
                          node name.
        -s --size         Size of the ping in bytes.
        -c --count        Number of pings to send.

    Example:
    $ happy-ping ThreadNode BorderRouter
        Sends a ping between the ThreadNode and BorderRouter nodes.

    return:
        0-100   percentage of the lost packets
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.source = opts["source"]
        self.destination = opts["destination"]
        self.count = opts["count"]
        self.size = opts["size"]

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.source:
            emsg = "Missing name of the virtual source node."
            self.logger.error("[localhost] Ping: %s" % (emsg))
            self.exit()

        # Check if the source node exists.
        if not self._nodeExists(self.source):
            emsg = "virtual source node %s does not exist." % (self.source)
            self.logger.error("[%s] Ping: %s" % (self.source, emsg))
            self.exit()

        # Check if the ping destination is given.
        if not self.destination:
            emsg = "Missing destination for ping."
            self.logger.error("[localhost] Ping: %s" % (emsg))
            self.exit()

        # Check if the destination node exists.
        if not self.isIpAddress(self.destination) and not self._nodeExists(self.destination):
            emsg = "virtual destination node %s does not exist." % (self.destination)
            self.logger.error("[%s] Ping: %s" % (self.source, emsg))
            self.exit()

        if self.count is not None and self.count.isdigit():
            self.count = int(float(self.count))
        else:
            self.count = 1

    def __get_addresses(self):
        self.addresses = {}

        if self.isIpAddress(self.destination):
            self.addresses[self.destination] = 100
            return

        if self._nodeExists(self.destination):
            node_addresses = self.getNodeAddresses(self.destination)

            for addr in node_addresses:
                self.addresses[addr] = 100

    def __ping_on_address(self, addr):
        cmd = ""

        if self.isIpv6(addr):
            cmd += "ping6"
        else:
            cmd += "ping"

        cmd += " -c " + str(self.count)

        if self.size is not None:
            cmd += " -s " + str(self.size)

        if self.isMulticast(addr):
            cmd += ""

        cmd += " " + addr

        out, err = self.CallAtNodeForOutput(self.source, cmd)

        return (out, err)

    def __parse_output(self, addr, out, err):
        if out is None:
            emsg = "Failed to call ping at node " + self.source + " to " + addr + "."
            self.logger.warning("[%s] Ping: %s" % (self.source, emsg))

            if err is not None:
                self.logger.warning("[%s] Ping: %s" % (self.source, err))

            return

        for line in out.split("\n"):
            if "packet loss" not in line:
                continue

            l = line.split()

            perc_loss = -1

            if len(l) > 10 and l[8] == "packet" and l[9] == "loss,":
                perc_loss = l[7]
                perc_loss = l[7][:-1]  # drop % char
                perc_loss = int(float(perc_loss))

            if len(l) > 8 and l[6] == "packet" and l[7] == "loss,":
                perc_loss = l[5]
                perc_loss = l[5][:-1]  # drop % char
                perc_loss = int(float(perc_loss))

            self.addresses[addr] = perc_loss
            break

    def __post_check(self):
        # pick the best result

        self.rets = []
        for addr in self.addresses.keys():
            self.rets.append(self.addresses[addr])

        if len(self.rets) > 0:
            self.ret = min(self.rets)
        else:
            self.ret = 100

    def run(self):
        self.__pre_check()

        self.__get_addresses()

        if self.addresses == {}:
            emsg = "No address to ping at " + str(self.destination) + "."
            self.logger.warning("[%s] Ping: %s" % (self.source, emsg))
            print hyellow(emsg)
            return ReturnMsg(100, self.addresses)

        for addr in self.addresses.keys():
            out, err = self.__ping_on_address(addr)
            self.__parse_output(addr, out, err)

        self.__post_check()

        for addr in self.addresses.keys():
            if self.isIpAddress(self.destination):
                self.logger.info("ping from " + self.source + " to address " +
                                 addr + " -> " + str(self.addresses[addr]) +
                                 "% packet loss")
            else:
                self.logger.info("ping from " + self.source + " to " + self.destination +
                                 " on address " + addr + " -> " + str(self.addresses[addr]) +
                                 "% packet loss")

        return ReturnMsg(self.ret, self.addresses)
