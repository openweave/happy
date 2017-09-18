#!/usr/bin/env python

#
#    Copyright (c) 2016-2017 Nest Labs, Inc.
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
#       Implements HappyNetworkRoute class that controls network gateway.
#
#       A virtual network is logical representation of a virtual ethernet
#       bridge that acts like a hub.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNetwork import HappyNetwork
from happy.HappyNode import HappyNode
import happy.HappyNodeRoute

options = {}
options["quiet"] = False
options["network_id"] = None
options["add"] = False
options["delete"] = False
options["to"] = None
options["via"] = None
options["prefix"] = None
options["record"] = True
options["isp"] = None
options["seed"] = None


def option():
    return options.copy()


class HappyNetworkRoute(HappyNetwork, HappyNode):
    """
    happy-network-route manages network IP routes.

    happy-network-route [-h --help] [-q --quiet] [-i --id <NETWORK_NAME>]
                      [-a --add] [-d --delete] [-t --to <ADDRESS>] [-v --via <ADDRESS>]
                      [-p --prefix <ADDRESS>] [-s --isp <ISP>] [-e --seed <SEED>]

                  The <ADDRESS> in  --to  can be IP address or 'default'.
                  The <ADDRESS> in  --via  can be IP address or <NODE_NAME>.
                  The <ISP> in --current ethernet's provider
                  The <SEED> in --priority can be the number <0-255> for the route table
    Example:
    $ happy-network-route Home default 2002:0:1:1::1
        Network Home get default route through 2002:0:1:1::1 address.
    $ happy-node-route node_01 default 2002:0:1:1::1 isp="ethernet" seed=100
        Node node_01 get default route through 2002:0:1:1::1 address and also route via the ethernet_table

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.network_id = opts["network_id"]
        self.add = opts["add"]
        self.delete = opts["delete"]
        self.to = opts["to"]
        self.via = opts["via"]
        self.prefix = opts["prefix"]
        self.record = opts["record"]
        self.isp = opts["isp"]
        self.seed = opts["seed"]
        self.via_node = None

    def __pre_check(self):
        # Check if the name of the new network is given
        if not self.network_id:
            emsg = "Missing name of the virtual network that should be configured with a route."
            self.logger.error("[localhost] HappyNetworkRoute: %s" % (emsg))
            self.exit()

        # Check if the name of new network is not a duplicate (that it does not already exists).
        if not self._networkExists():
            emsg = "virtual network %s does not exist." % (self.network_id)
            self.logger.error("[%s] HappyNetworkRoute: %s" % (self.network_id, emsg))
            self.exit()

        if not self.delete:
            self.add = True

        # Check if 'to' is given
        if not self.to:
            emsg = "Missing destination address for virtual network (to)."
            self.logger.error("[%s] HappyNetworkRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check if 'via' is given
        if not self.via:
            emsg = "Missing gateway address for virtual network (via)."
            self.logger.error("[%s] HappyNetworkRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check for mix IP addresses
        if self.isIpAddress(self.to) and self.isIpAddress(self.via) and self.isIpv6(self.to) != self.isIpv6(self.via):
            emsg = "Mixing addresses %s and %s." % (self.to, self.via)
            self.logger.error("[%s] HappyNetworkRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check if destination is a node
        if self.to != "default" and not self.isIpAddress(self.to):
            if not self._nodeExists(self.to):
                emsg = "Don't know what %s to-address is. If it is a node, it can't be found." % (self.to)
                self.logger.error("[localhost] HappyNetworkRoute: %s" % (emsg))
                self.exit()
            else:
                # 'to' is a node
                emsg = "Destination address must be 'default' or a IP address."
                self.logger.error("[localhost] HappyNetworkRoute: %s" % (emsg))
                self.exit()

        if self.isIpAddress(self.to):
            self.to = self.paddingZeros(self.to)

        # Check if gateway is an address or a node
        if self.isIpAddress(self.via):
            self.via = self.paddingZeros(self.via)
            self.via_node = self.getNodeIdFromAddress(self.via)

            if self.via_node is None or not self._nodeExists(self.via_node):
                emsg = "Cannot find a node that would match %s." % (self.via)
                self.logger.error("[localhost] HappyNetworkRoute: %s" % (emsg))
                self.exit()

            return

        if self._nodeExists(self.via):
            self.via_node = self.via

    def __configure_nodes_routes(self):
        for node_id in self.getNetworkNodesIds(self.network_id):
            if self.via_node is not None and node_id == self.via_node:
                continue

            options = happy.HappyNodeRoute.option()
            options["quiet"] = self.quiet
            options["node_id"] = node_id
            options["to"] = self.to
            options["via"] = self.via
            options["prefix"] = self.prefix
            options["record"] = self.record
            options["isp"] = self.isp
            options["seed"] = self.seed

            if self.add:
                options["add"] = True
            else:
                options["delete"] = True

            routeCtrl = happy.HappyNodeRoute.HappyNodeRoute(options)
            ret = routeCtrl.run()

            self.readState()

    def __configure_gateway_routing(self):
        if self.via_node is None:
            return

        self.nodeIPv4Forwarding(1, self.via_node)
        self.nodeIPv6Forwarding(1, self.via_node)

        node_type = self.getNodeType(self.via_node)
        if node_type != self.node_type_ap:
            return

        for interface_id in self.getNodeInterfaceIds(self.via_node):
            interface_type = self.getNodeInterfaceType(interface_id, self.via_node)
            if interface_type != self.network_type["wan"]:
                continue

            self.setNATonInterface(interface_id, self.via_node)

    def __post_check(self):
        pass

    def __update_state(self):
        if not self.record:
            return

        if self.add:
            new_route = {}
            new_route["to"] = self.to
            new_route["via"] = self.via
            new_route["prefix"] = self.prefix

            self.setNetworkRoute(self.network_id, self.to, new_route)
        else:
            self.removeNetworkRoute(self.network_id, self.to)

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

        self.__configure_nodes_routes()

        self.__configure_gateway_routing()

        with self.getStateLockManager():

            self.__post_check()

            self.readState()

            self.__update_state()

            self.writeState()

        return ReturnMsg(0)
