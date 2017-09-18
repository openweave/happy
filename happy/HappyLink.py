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
#       Implements HappyLink class that provides virtual Link abstraction.
#
#       Virtual Link-specific actions inherit from this class.
#

import os
import sys

from happy.Utils import *
from happy.HappyHost import HappyHost


class HappyLink(HappyHost):
    def __init__(self, link_id=None):
        HappyHost.__init__(self)
        self.link_id = link_id

    def _linkExists(self, link_id=None):
        if link_id is None:
            link_id = self.link_id

        link_id = self.uniquePrefix(link_id)
        link_id_net = self.getUniqueLinkNetworkEnd()
        link_id_node = self.getUniqueLinkNodeEnd()

        host_links = self.getHostInterfaces()

        if link_id in host_links:
            return True

        if link_id_net in host_links:
            return True

        if link_id_node in host_links:
            return True

        for network_id in self.getNetworkIds():
            network_links = self.getActiveNetworkLinks(network_id)
            if link_id_net in network_links:
                return True

        return False

    def getUniqueLinkNetworkEnd(self, link_id=None):
        if link_id is None:
            link_id = self.link_id

        return self.uniquePrefix(link_id + self.network_link_suffix)

    def getUniqueLinkNodeEnd(self, link_id=None):
        if link_id is None:
            link_id = self.link_id

        return self.uniquePrefix(link_id + self.node_link_suffix)

    def getTapBridgeId(self, link_id=None):
        if link_id is None:
            link_id = self.link_id

        return self.uniquePrefix(link_id + self.ethernet_bridge_suffix)

    def getTapLinkId(self, link_id=None):
        if link_id is None:
            link_id = self.link_id

        return self.uniquePrefix(link_id + self.ethernet_bridge_link)

    def moveInterfaceToNamespace(self, link_name, node_id):
        namespace_id = self.uniquePrefix(node_id)
        cmd = "ip link set " + link_name + " netns " + namespace_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def moveBridgeToNamespace(self, bridge_id, node_id):
        cmd = "ip link delete " + bridge_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link add " + bridge_id + " type bridge"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(node_id, cmd)

    def moveLwipInterfaceToNamespace(self, link_id, node_id):
        link_node_end = self.getLinkNodeEnd(link_id)
        eth_link_id = self.getTapLinkId(link_id)
        eth_bridge_id = self.getTapBridgeId(link_id)

        self.moveInterfaceToNamespace(link_node_end, node_id)
        self.moveInterfaceToNamespace(eth_link_id, node_id)
        self.moveBridgeToNamespace(eth_bridge_id, node_id)

        cmd = "ip link set " + link_node_end + " master " + eth_bridge_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(node_id, cmd)

        cmd = "ip link set " + eth_link_id + " master " + eth_bridge_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(node_id, cmd)

    def bringLinkUp(self, link_id, node_if_name, node_id, network_id):
        link_network_end = self.getLinkNetworkEnd(link_id)

        if self.getLinkTap(self.link_id):
            veth_id = self.getTapLinkId(link_id)
            cmd = "ifconfig " + veth_id + " up"
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(node_id, cmd)

            br_id = self.getTapBridgeId(link_id)
            cmd = "ifconfig " + br_id + " up"
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(node_id, cmd)

        # disable dad before the interface is brought up
        cmd = "sysctl net.ipv6.conf." + node_if_name + ".accept_dad=0"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(node_id, cmd)

        cmd = "ifconfig " + node_if_name + " up"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(node_id, cmd)

        cmd = "ifconfig " + link_network_end + " up"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNetwork(network_id, cmd)

        # We have disabled DAD, but under high load we can still see the
        # address in "tentative" for a few milliseconds.
        # If DAD is re-enabled, we should poll all interfaces at once after the topology
        # has been brought up, so the interfaces can come up in parallel.
        self.waitForDAD()
