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
#       Implements HappyNodeLeave class through which a virtual node leaves a network.
#
#       When a node joins a network, an TAP interface is created in the node and in
#       the network. Then TUN is setup on the node.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyLink import HappyLink
from happy.HappyNetwork import HappyNetwork
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["node_id"] = None
options["network_id"] = None


def option():
    return options.copy()


class HappyNodeLeave(HappyNode, HappyNetwork):
    """
    Removes a virtual node from a specific network or all networks.

    happy-node-leave [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                     [-n --network <NETWORK_NAME>]

        -i --id         Required. Node to remove from a network. Find using
                        happy-node-list or happy-state.
        -n --network    Network to remove the node from. Find using
                        happy-network-list or happy-state.

    Examples:
    $ happy-node-leave ThreadNode HomeThread
        Removes the ThreadNode node from the HomeThread network.

    $ happy-node-leave ThreadNode
        Removes the ThreadNode node from all networks.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.network_id = opts["network_id"]

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should join a network."
            self.logger.error("[localhost] HappyNodeLeave: %s" % (emsg))
            self.exit()

        # Check if node exists
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyNodeLeave: %s" % (self.node_id, emsg))
            self.exit()

        # Check if network exists
        if self.network_id is not None and not self._networkExists():
            emsg = "virtual network %s does not exist." % (self.network_id)
            self.logger.error("[%s] HappyNodeLeave: %s" % (self.network_id, emsg))
            self.exit()

    def __leave(self):
        if self.network_id:
            self.delete_node_from_network(self.network_id)
        else:
            self.DeleteNodeInterfaces()

    def __post_check(self):
        for link_id in self.getNodeLinkIds():
            if link_id in self.getNetworkLinkIds():
                emsg = "Node %s failed to leave network %s." % (self.node_id, self.network_id)
                self.logger.error("[%s] HappyNodeLeave: %s" % (self.node_id, emsg))
                self.exit()

    def run(self):
        self.__pre_check()

        self.__leave()

        self.__post_check()

        return ReturnMsg(0)
