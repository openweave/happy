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
#       Implements HappyNodeJoin class through which a virtual node join a network.
#
#       When a node joins a network, an TAP interface is created in the node and in
#       the network. Then TUN is setup on the node.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.utils.IP import IP
from happy.HappyLink import HappyLink
from happy.HappyNetwork import HappyNetwork
from happy.HappyNode import HappyNode
import happy.HappyLinkAdd
import happy.HappyNodeAddress
import happy.HappyNodeRoute

options = {}
options["quiet"] = False
options["node_id"] = None
options["tap"] = False
options["network_id"] = None
options["fix_hw_addr"] = None
options["customized_eui64"] = None


def option():
    return options.copy()


class HappyNodeJoin(HappyLink, HappyNode, HappyNetwork):
    """
    Assigns a virtual node to a specific network.

    happy-node-join [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                    [-n --network <NETWORK_NAME>] [-m --mac <HW_ADDR>]
                    [-c --customizedeui64 <CUST_EUI64>] [-p --tap]

        -i --id              Required. Node to be added to a network. Find using
                             happy-node-list or happy-state.
        -n --network         Required. Network to add the node to. Find using
                             happy-network-list or happy-state.
        -m --mac             The MAC hardware address for the node.
        -c --customizedeui64 The EUI64 address for the node.
        -p --tap             Configure the link between the node and the network as an
                             L2 TAP device with a virtual bridge. Omit this parameter to
                             default to an L3 TUN configuration for normal IP routing.

    Example:
    $ happy-node-join ThreadNode HomeThread
        Adds the ThreadNode node to the HomeThread network.

    $ happy-node-join -i onhub -n HomeWiFi -m 5
        Adds the onhub node to the HomeWiFi network with a MAC hardware address of
        00:00:00:00:00:05.

    $ happy-node-join -i onhub -n HomeWiFi -c 00:00:00:00:00:00:00:05
        Adds the onhub node to the HomeWiFi network with an EUI64 address of
        00:00:00:00:00:00:00:05.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)
        HappyNode.__init__(self)
        HappyLink.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.tap = opts["tap"]
        self.network_id = opts["network_id"]
        self.fix_hw_addr = opts["fix_hw_addr"]
        self.customized_eui64 = opts["customized_eui64"]
        if not self.fix_hw_addr and opts["customized_eui64"]:
            self.fix_hw_addr = self.customized_eui64[6:]
            self.customized_eui64 = self.customized_eui64.replace(':', '-')

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should join a network."
            self.logger.error("[localhost] HappyNodeJoin: %s" % (emsg))
            self.exit()

        # Check if the name of the network is given
        if not self.network_id:
            emsg = "Missing name of the virtual network that be joined by a virtual node."
            self.logger.error("[localhost] HappyNodeJoin: %s" % (emsg))
            self.exit()

        # Check if node exists
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

        # Check if network exists
        if not self._networkExists():
            emsg = "virtual network %s does not exist." % (self.network_id)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

        # Check if node already joined that network
        if self.network_id in self.getNodeNetworkIds():
            emsg = "virtual node %s is already part of %s network." % (self.node_id, self.network_id)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

        self.fix_hw_addr = self.fixHwAddr(self.fix_hw_addr)
        # Check if HW MAC address is valid
        if self.fix_hw_addr is not None and self.fix_hw_addr.count(":") != 5:
            emsg = "virtual node %s get invalid MAC HW address %s." % (self.node_id, self.fix_hw_addr)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

    def __create_link(self):

        options = happy.HappyLinkAdd.option()
        options["quiet"] = self.quiet
        options["type"] = self.getNetworkType()
        options["tap"] = self.tap

        link = happy.HappyLinkAdd.HappyLinkAdd(options)
        ret = link.run()
        self.link_id = ret.Data()

        self.readState()

    def __post_check_1(self):
        # Ensure that the link is saved in the state
        if self.link_id not in self.getLinkIds():
            emsg = "Link %s does not exist." % (self.link_id)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

    def __get_node_interface_info(self):
        self.link_type = self.getLinkType(self.link_id)
        self.link_network_end = self.getLinkNetworkEnd(self.link_id)
        self.link_node_end = self.getLinkNodeEnd(self.link_id)
        self.node_interface_name = self.getNodeInterfaceName(self.node_id, self.link_type)

    def __connect_to_network(self):
        self.moveInterfaceToNamespace(self.link_network_end, self.network_id)

        # Attach to bridge
        cmd = "brctl addif " + self.uniquePrefix(self.network_id) + " " + self.link_network_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(self.network_id, cmd)

    def __connect_to_node(self):
        if not self.isNodeLocal(self.node_id):
            if self.getLinkTap(self.link_id):
                self.moveLwipInterfaceToNamespace(self.link_id, self.node_id)
            else:
                self.moveInterfaceToNamespace(self.link_node_end, self.node_id)

        cmd = "ip link set " + self.link_node_end
        cmd += " name " + self.node_interface_name

        if self.fix_hw_addr is not None:
            cmd += " address " + self.fix_hw_addr

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNode(self.node_id, cmd)

    def __nmconf(self):
        if not self.isNodeLocal(self.node_id):
            return

        if not self.tap:
            cmd = "nmcli dev disconnect iface " + self.node_interface_name
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

    def __check_node_hw_addr(self):
        hw_addr = self.getHwAddress(self.node_interface_name, self.node_id)
        hw_addr_int = IP.mac48_string_to_int(hw_addr)

        if (hw_addr_int & (1 << 41)):
            hw_addr_int = hw_addr_int & ~(1 << 41)
            new_hw_addr = IP.mac48_string_to_int(hw_addr_int)

            cmd = "ip link set " + self.node_interface_name + " address " + str(new_hw_addr)
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(self.node_id, cmd)

    def __post_check_2(self):
        return

    def __bring_up_interface(self):
        self.bringLinkUp(self.link_id, self.node_interface_name, self.node_id, self.network_id)

    def __add_new_interface_state(self):
        self.setLinkNetworkNodeHw(self.link_id, self.network_id, self.node_id, self.fix_hw_addr)

        new_network_interface = {}
        self.setNetworkLink(self.network_id, self.link_id, new_network_interface)

        new_node_interface = {}
        new_node_interface["link"] = self.link_id
        new_node_interface["type"] = self.link_type
        new_node_interface["ip"] = {}
        if self.customized_eui64:
            new_node_interface["customized_eui64"] = self.customized_eui64
        self.setNodeInterface(self.node_id, self.node_interface_name, new_node_interface)

    def __assign_network_addresses(self):
        network_prefixes = self.getNetworkPrefixes(self.network_id)

        for prefix in network_prefixes:
            options = happy.HappyNodeAddress.option()
            options["quiet"] = self.quiet
            options["node_id"] = self.node_id
            options["interface"] = self.node_interface_name

            if IP.isIpv6(prefix):
                nid = self.getInterfaceId(self.node_interface_name, self.node_id)
            else:
                nid = self.getNextNetworkIPv4Id(prefix, self.network_id)

            options["address"] = self.getNodeAddressOnPrefix(prefix, nid)

            options["add"] = True

            addrctrl = happy.HappyNodeAddress.HappyNodeAddress(options)

            ret = addrctrl.run()

    def __load_network_routes(self):
        routes = self.getNetworkRoutes(self.network_id)
        for route_to in routes.keys():
            route_record = self.getNetworkRoute(route_to, self.network_id)

            options = happy.HappyNodeRoute.option()
            options["quiet"] = self.quiet
            options["add"] = True

            options["node_id"] = self.node_id
            options["to"] = route_to
            options["via"] = route_record["via"]
            options["prefix"] = route_record["prefix"]

            noder = happy.HappyNodeRoute.HappyNodeRoute(options)
            ret = noder.run()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.__create_link()

            self.__post_check_1()

            self.__get_node_interface_info()

            self.__connect_to_network()

            self.__connect_to_node()

            self.__nmconf()

            self.__check_node_hw_addr()

            self.__bring_up_interface()

            self.__post_check_2()

            self.__add_new_interface_state()

            self.writeState()

        self.__assign_network_addresses()

        self.__load_network_routes()

        return ReturnMsg(0)
