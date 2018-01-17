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
#       Implements HappyNetworkAddress class that assigns a network prefix address.
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
import happy.HappyNodeAddress

options = {}
options["quiet"] = False
options["network_id"] = None
options["add"] = False
options["delete"] = False
options["address"] = None


def option():
    return options.copy()


class HappyNetworkAddress(HappyNetwork, HappyNode):
    """
    happy-network-address manages network prefixes.

    happy-network-address [-h --help] [-q --quiet] [-i --id <NETWORK_NAME>]
                      [-a --add] [-d --delete] [<ADDRESS>]

    Example:
    $ happy-network-address Home fd00:1:2:3::/64
        Assigns network Home prefix fd00:1:2:3:: and mask 64. All nodes that are
        already part of this network will get an IP address with that prefix.

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
        self.address = opts["address"]

    def __pre_check(self):
        # Check if the name of the new network is given
        if not self.network_id:
            emsg = "Missing name of the new virtual network that should be created."
            self.logger.error("[localhost] HappyNetworkAddress: %s" % (emsg))
            self.exit()

        # Check if the name of new network is not a duplicate (that it does not already exists).
        if not self._networkExists():
            emsg = "virtual network %s does not exist." % (self.network_id)
            self.logger.warning("[%s] HappyNetworkAddress: %s" % (self.network_id, emsg))
            self.exit()

        # Check if address is given
        if not self.address:
            emsg = "Missing IP preifx for network %s." % (self.network_id)
            self.logger.error("[%s] HappyNetworkAddress: %s" % (self.network_id, emsg))
            self.exit()

        self.ip_prefix, self.ip_mask = self.splitAddressMask(self.address)
        self.ip_prefix = self.getPrefix(self.ip_prefix, self.ip_mask)

        # Check if successfully parsed prefix
        if self.ip_prefix is None or self.ip_mask is None:
            emsg = "Did not understand address format %s." % (self.address)
            self.logger.error("[%s] HappyNetworkAddress: %s" % (self.network_id, emsg))
            self.exit()

        if not self.delete:
            self.add = True

        # Check if network has given prefix
        if self.delete and self.ip_prefix not in self.getNetworkPrefixes():
            emsg = "Network %s may not have prefix %s." % (self.network_id, self.ip_prefix)
            self.logger.warning("[%s] HappyNetworkAddress: %s" % (self.network_id, emsg))

    def __configure_node_address(self):
        network_links = self.getNetworkLinkIds(self.network_id)

        for link_id in network_links:
            node_id = self.getLinkNode(link_id)

            options = happy.HappyNodeAddress.option()
            options["quiet"] = self.quiet
            options["node_id"] = node_id

            interface_id = self.getNodeInterfaceFromLink(link_id, node_id)
            options["interface"] = interface_id

            if self.isIpv6(self.address):
                nid = self.getInterfaceId(interface_id, node_id)
            else:
                nid = self.getNextNetworkIPv4Id(self.ip_prefix, self.network_id)

            options["address"] = self.getNodeAddressOnPrefix(self.ip_prefix, nid)

            if self.add:
                options["add"] = True
            else:
                options["delete"] = True

            addrctrl = happy.HappyNodeAddress.HappyNodeAddress(options)
            ret = addrctrl.run()

            self.readState()

    def __post_check(self):
        pass

    def __update_state(self):
        if self.add:
            new_prefix = {}
            new_prefix["mask"] = int(float(self.ip_mask))

            self.setNetworkPrefix(self.network_id, self.ip_prefix, new_prefix)
        else:
            self.removeNetworkPrefix(self.network_id, self.ip_prefix)

    def run(self):
        self.__pre_check()

        self.__configure_node_address()

        self.__post_check()

        with self.getStateLockManager():
            self.readState()

            self.__update_state()

            self.writeState()

        return ReturnMsg(0)
