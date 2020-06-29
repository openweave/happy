#!/usr/bin/env python3

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
#       Implements HappyNodeAddress class that manipulates virtual node IP addresses.
#
#       This is a wrapper around Linux ip-address command.
#

from __future__ import absolute_import
from __future__ import print_function
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.utils.IP import IP
from happy.HappyNode import HappyNode
import json

options = {}
options["quiet"] = False
options["node_id"] = None
options["interface"] = None
options["add"] = False
options["delete"] = False
options["address"] = None


def option():
    return options.copy()


class HappyNodeAddress(HappyNode):
    """
    Manages virtual node IP addresses.

    happy-node-address [-h --help] [-q --quiet] [-a --add] [-d --delete]
                       [-i --id <NODE_NAME>] [-e --interface <IFACE>] [<IP_ADDR>]

        -i --id         Required. Node to manage addresses for. Find using
                        happy-node-list or happy-state.
        -e --interface  Interface to bind the address to.

    Examples:
    $ happy-node-address BorderRouter wpan0 fd00:0:1:1::1
        Adds an IP address of fd00:0:1:1::1 to the wpan0 interface of the
        BorderRouter node.

    $ happy-node-address -d BorderRouter wpan0 fd00:0:1:1::1
        Deletes the IP address of fd00:0:1:1::1 from the wpan0 interface of the
        BorderRouter node.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.interface = opts["interface"]
        self.add = opts["add"]
        self.delete = opts["delete"]
        self.address = opts["address"]
        self.done = False

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the new virtual node that IP address should be managed."
            self.logger.error("[localhost] HappyNodeAddress: %s" % (emsg))
            self.exit()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.warning("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))

        # Check if the name of the interface is given
        if not self.interface:
            emsg = "Missing name of the network interface in virtual node."
            self.logger.error("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.exit()

        # Check if node has a given interface
        if not self._nodeInterfaceExists(self.interface, self.node_id):
            emsg = "virtual node %s does not have interface %s." % (self.node_id, self.interface)
            self.logger.warning("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.exit()

        # Check if address is given
        if not self.address:
            emsg = "Missing IP address for virtual node."
            self.logger.error("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.exit()

        self.ip_address, self.ip_mask = IP.splitAddressMask(self.address)
        self.ip_address = IP.paddingZeros(self.ip_address)

        if not self.delete:
            self.add = True

        # Check if node has given prefix
        addr_prefix = IP.getPrefix(self.ip_address, self.ip_mask)
        if self.delete and addr_prefix not in self.getNodeInterfacePrefixes(self.interface):
            emsg = "virtual node %s may not have any addresses on prefix %s." % (self.node_id, addr_prefix)
            self.logger.warning("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))

        # Check if node has this address already
        if self.add and self.address in self.getNodeInterfaceAddresses(self.interface):
            emsg = "virtual node %s already has addresses %s." % (self.node_id, self.address)
            self.logger.error("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.done = True

    def __add_address(self):
        cmd = "ip "

        if IP.isIpv6(self.address):
            cmd += "-6 "

        cmd += "addr add " + str(self.ip_address) + "/" + str(self.ip_mask) + " dev " + self.interface

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNode(self.node_id, cmd)

        # We have disabled DAD, but under high load we can still see the
        # address in "tentative" for a few milliseconds.
        # If DAD is re-enabled, we should poll all interfaces at once after the topology
        # has been brought up, so the interfaces can come up in parallel.
        self.waitForDAD()

    def __delete_address(self):
        cmd = "ip "
        if IP.isIpv6(self.address):
            cmd += "-6 "
        cmd += "addr del " + str(self.ip_address) + "/" + str(self.ip_mask) + " dev " + self.interface

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNode(self.node_id, cmd)

    def __post_check(self):
        ipaddrs = self.getIpAddresses(self.interface, self.node_id)

        has_ip = False

        for iaddr in ipaddrs:
            addr_part, _ = IP.splitAddressMask(iaddr)
            if self.ip_address == addr_part:
                has_ip = True
                break

        if self.add and not has_ip:
            emsg = "Failed to add IP address %s to node %s, interface %s." % \
                (self.address, self.node_id, self.interface)
            self.logger.error("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.exit()

        if self.delete and has_ip:
            emsg = "Failed to delete IP address %s from node %s, interface %s." % \
                (self.address, self.node_id, self.interface)
            self.logger.error("[%s] HappyNodeAddress: %s" % (self.node_id, emsg))
            self.exit()

    def __update_state(self):
        if self.add:
            new_ip = {}
            new_ip["mask"] = self.ip_mask
            self.setNodeIpAddress(self.node_id, self.interface, self.ip_address, new_ip)
        else:
            self.removeNodeInterfaceAddress(self.node_id, self.interface, self.ip_address)

    def run(self):
        if not self.add and not self.delete:
            data_state = json.dumps(self.getNodeInterfaceAddresses(self.interface, self.node_id), sort_keys=True, indent=4)

            emsg = "virtual node: " + self.node_id + " addresses list for interface id: " + self.interface

            print(emsg)
            print(data_state)

        else:
            with self.getStateLockManager():

                self.__pre_check()

                if not self.done:
                    if not self.IsTapDevice(self.node_id):
                        if self.add:
                            self.__add_address()
                        else:
                            self.__delete_address()

                        self.__post_check()

                    self.__update_state()

                    self.writeState()

        return ReturnMsg(0)
