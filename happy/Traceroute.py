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
#       Implements Traceroute class that call traceroute to a virtual nodes.
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


def option():
    return options.copy()


class Traceroute(HappyNode):
    """
    Calls traceroute between virtual nodes. Uses traceroute for IPv4 and traceroute6
    for IPv6.

    happy-traceroute [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                     [-d --destination (<IP_ADDR>|<NODE_NAME>)]

        -i --id           Source node.
        -d --destination  Destination, can be either the IP address or the node name.

    Example:
    $ happy-traceroute BorderRouter ThreadNode
        Calls traceroute between the BorderRouter and ThreadNode nodes.

    $ happy-traceroute BorderRouter 10.0.1.3
        Calls traceroute between the BorderRouter node and 10.0.1.3.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.source = opts["source"]
        self.destination = opts["destination"]

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.source:
            emsg = "Missing name of the virtual source node."
            self.logger.error("[localhost] Traceroute: %s" % (emsg))
            self.exit()

        # Check if the source node exists.
        if not self._nodeExists(self.source):
            emsg = "virtual source node %s does not exist." % (self.source)
            self.logger.error("[%s] Traceroute: %s" % (self.source, emsg))
            self.exit()

        # Check if the traceroute destination is given.
        if not self.destination:
            emsg = "Missing destination for traceroute."
            self.logger.error("[localhost] Traceroute: %s" % (emsg))
            self.exit()

        # Check if the destination node exists.
        if not self.isIpAddress(self.destination) and not self._nodeExists(self.destination):
            emsg = "virtual destination node %s does not exist." % (self.destination)
            self.logger.error("[%s] Traceroute: %s" % (self.source, emsg))
            self.exit()

    def __get_addresses(self):
        self.addresses = {}

        if self.isIpAddress(self.destination):
            self.addresses[self.destination] = None
            return

        if self._nodeExists(self.destination):
            node_addresses = self.getNodeAddresses(self.destination)

            for addr in node_addresses:
                self.addresses[addr] = {}

    def __traceroute_to_address(self, addr):
        cmd = ""

        if self.isIpv6(addr):
            cmd += "traceroute6"
        else:
            cmd += "traceroute"

        if self.isMulticast(addr):
            cmd += ""

        cmd += " " + addr

        out, err = self.CallAtNodeForOutput(self.source, cmd)

        return (out, err)

    def __parse_output(self, addr, out, err):
        self.addresses[addr]["out"] = out
        self.addresses[addr]["err"] = err

        if out is not None:
            self.addresses[addr]["value"] = 0

            if "* * *" in self.addresses[addr]["out"]:
                return

            for line in self.addresses[addr]["out"].split("\n"):
                l = line.split()
                if len(l) > 1 and l[0].isdigit():
                    self.addresses[addr]["value"] = int(float(l[0]))

        else:
            self.addresses[addr]["value"] = -1

    def __post_check(self):
        # Check if at least one got to destination
        self.rets = []

        for addr in self.addresses.keys():
            if self.addresses[addr]["out"] is None:
                self.rets.append(0)
                continue

            if self.addresses[addr]["value"] < 1:
                self.rets.append(self.addresses[addr]["value"])
                continue

            self.rets.append(self.addresses[addr]["value"])

        if len(self.rets) > 0:
            self.ret = max(self.rets)
        else:
            self.ret = -1

    def run(self):
        self.__pre_check()

        self.__get_addresses()

        for addr in self.addresses.keys():
            out, err = self.__traceroute_to_address(addr)

            self.__parse_output(addr, out, err)

        self.__post_check()

        for addr in self.addresses.keys():
            self.logger.info("traceroute to " + addr + ":")

            if self.addresses[addr]["out"] is None:
                self.logger.info("\tNone")
            else:
                for line in self.addresses[addr]["out"].split("\n"):
                    self.logger.info("\t" + line)

        return ReturnMsg(self.ret, self.addresses)
