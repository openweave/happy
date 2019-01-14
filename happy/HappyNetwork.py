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
#       Implements HappyNetwork class that provides virtual networks abstraction.
#
#       virtual network-specific actions inherit from this class.
#

import os
import sys

from happy.Utils import *
from happy.utils.IP import IP
from happy.HappyHost import HappyHost
import happy.HappyLinkDelete


class HappyNetwork(HappyHost):
    def __init__(self, network_id=None):
        HappyHost.__init__(self)

        self.network_id = network_id

    def _networkExists(self, network_id=None):
        if network_id is None:
            network_id = self.network_id

        if self._namespaceExists(network_id):
            return self.uniquePrefix(network_id) in self._getNetworkBridges(network_id)

        return False

    def _getNetworkBridges(self, network_id=None):
        if network_id is None:
            network_id = self.network_id

        ret = []
        cmd = "brctl show"
        bridges, err = self.CallAtNetworkForOutput(network_id, cmd)
        bridges = bridges.split("\n")

        for record in bridges:
            r = record.split()
            if len(r) < 1:
                continue

            if r[0] == "bridge":
                continue

            ret.append(r[0])

        return ret

    def _networkState(self, network_id=None):
        if network_id is None:
            network_id = self.network_id

        cmd = "ip link show " + self.uniquePrefix(network_id)

        out, err = self.CallAtNetworkForOutput(network_id, cmd)

        if out is None:
            return 'UNKNOWN'

        out = out.split("\n")

        if len(out) < 2:
            return 'UNKNOWN'

        info = out[0].split()
        state = info[8]

        return state

    def typeToName(self, type):
        if type == self.network_type["thread"]:
            return "wpan"

        if type == self.network_type["wifi"]:
            return "wlan"

        if type == self.network_type["wan"]:
            return "eth"

        if type == self.network_type["cellular"]:
            return "ppp"

        if type == self.network_type["out-of-band"]:
            return "oob"

        return ""

    def _delete_network_interfaces(self):
        for link_id in self.getNetworkLinkIds():
            self._delete_network_link(link_id)

    def _delete_network_link(self, link_id):
        options = happy.HappyLinkDelete.option()
        options["quiet"] = self.quiet
        options["link_id"] = link_id
        cmd = happy.HappyLinkDelete.HappyLinkDelete(options)
        ret = cmd.run()

        self.readState()

    def getNextNetworkIPv4Id(self, prefix, network_id=None):
        if network_id is None:
            network_id = self.network_id

        network_links = self.getNetworkLinkIds(network_id)

        all_ips = []

        for node_id in self.getNodeIds():
            node_links = self.getNodeLinkIds(node_id)
            link_ids = list(set(network_links).intersection(node_links))

            node_ips = []
            for link_id in link_ids:
                interface_id = self.getNodeInterfaceFromLink(link_id, node_id)
                node_ips += self.getNodeInterfaceAddresses(interface_id, node_id)

            all_ips += node_ips

        ids = []

        prefix_list = prefix.split(".")
        if len(prefix_list) < 3:
            print hred("Invalid prefix %s, guessing id" % (prefix))
            return 100

        for ip in all_ips:
            if IP.isIpv6(ip):
                continue

            ip_list = ip.split(".")

            if prefix_list[0] != ip_list[0] or prefix_list[1] != ip_list[1] or \
               prefix_list[2] != ip_list[2]:
                continue

            ids.append(int(ip_list[3]))

        if ids == []:
            # Start addresses from 2
            return 2

        ids.sort()

        return ids[-1] + 1
