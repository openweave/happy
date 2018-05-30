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
#       Implements HappyLinkAdd class that creates virtual nodes.
#
#       A virtual node is a logical representation of a network namespace.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyLink import HappyLink
import happy.HappyLinkDelete

options = {}
options["quiet"] = False
options["type"] = None
options["tap"] = False


def option():
    return options.copy()


class HappyLinkAdd(HappyLink):
    """
    Creates a new link that connects a virtual node to a network. A virtual node
    is a logical representation of a network namespace.

    happy-link-add [-h --help] [-q --quiet] [-p --tap]
                   [-t --type (cellular|out-of-band|thread|wan|wifi)]

        -p --tap    Configure the link as an L2 TAP device with a virtual bridge.
                    Omit this parameter to default to an L3 TUN configuration for
                    normal IP routing.
        -t --type   Required. Type of link to add.

    Examples:
    $ happy-link-add thread
        Creates a new Thread (wpan) network link.

    $ happy-link-add -p wan
        Creates a new WAN (eth) TAP network bridge.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyLink.__init__(self)

        self.quiet = opts["quiet"]
        self.type = opts["type"]
        self.tap = opts["tap"]

        self.link_number = None
        self.link_id = None

        self.link_network_end = None
        self.link_node_end = None

    def __deleteExistingLink(self):

        options = happy.HappyLinkDelete.option()
        options["link_id"] = self.link_id
        options["quiet"] = self.quiet
        delLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        delLink.run()

        self.readState()

    def __pre_check(self):
        # Check if the name of the new link is given
        if not self.type:
            emsg = "Missing the type of the new virtual link that should be created."
            self.logger.error("[%s] HappyLinkAdd: %s" % ("Link", emsg))
            self.exit()

        self.type = self.type.lower()

        if self.type not in self.network_type.keys():
            emsg = "Invalid link type " + self.type
            self.logger.error("[%s] HappyLinkAdd: %s" % ("Link", emsg))
            self.exit()

    def __get_link_number(self):
        existing_numbers = []

        for link_id in self.getLinkIds():
            if self.getLinkType(link_id) == self.type:
                existing_numbers.append(self.getLinkNumber(link_id))

        if len(existing_numbers) == 0:
            return 0

        existing_numbers.sort()

        if existing_numbers[0] > 0:
            return existing_numbers[0] - 1

        for idx in range(len(existing_numbers) - 1):
            if existing_numbers[idx+1] - existing_numbers[idx] > 1:
                return existing_numbers[idx] + 1

        return existing_numbers[-1] + 1

    def __get_link_id(self):
        self.link_id = self.type + str(self.link_number)

    def __get_link_ends(self):
        self.link_node_end = self.getUniqueLinkNodeEnd()
        self.link_network_end = self.getUniqueLinkNetworkEnd()

        self.eth_link_id = self.getTapLinkId(self.link_id)
        self.eth_bridge_id = self.getTapBridgeId(self.link_id)

    def __check_if_link_exists(self):
        if self._linkExists():
            emsg = "virtual link %s already exists." % (self.link_id)
            self.logger.warning("[%s] HappyNodeAdd: %s" % (self.link_id, emsg))
            self.__deleteExistingLink()

    def __create_tap_link(self):
        # TAP interfaces use a bridge at the node's namespace to attach a tap interface
        # and use veth link between the node's bridge and a network
        #
        #         a node                                        a network
        #
        #  <state_id><type><#>o                         --- <state_id><type><#>n
        #                     |                        /
        #    bridge at node   |                       /
        #                     |                      /
        #  <state_id><type><#>b-<state_id><type><#>v-
        #
        # e.g.
        #
        # happythread0o                - happythread0n
        #         |                   /
        # happythread0b-happythread0v-
        #

        cmd = "ip tuntap add " + self.link_node_end + " mode tap"
        if "USER" in os.environ.keys():
            cmd += " user " + os.environ["USER"]
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link add " + self.eth_bridge_id + " type bridge"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link add name " + self.eth_link_id \
            + " type veth peer name " + self.link_network_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set dev " + self.eth_bridge_id + " up"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set dev " + self.eth_link_id + " up"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set " + self.link_node_end + " master " + self.eth_bridge_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set " + self.eth_link_id + " master " + self.eth_bridge_id
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __create_veth_link(self):
        # TUN links use veth inerfaces between a node and a network
        #
        #         a node                   a network
        #
        #  <state_id><type><#>o ------ <state_id><type><#>n
        #
        # eg.
        #       happythread0o --------- happythread0n
        #
        cmd = "ip link add name " + self.link_node_end \
            + " type veth peer name " + self.link_network_end

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __create_link(self):
        if self.tap:
            self.__create_tap_link()
        else:
            self.__create_veth_link()

    def __turn_down_link_ends(self):
        cmd = "ip link set " + self.link_node_end + " down"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set " + self.link_network_end + " down"
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __post_check(self):
        if not self._linkExists(self.link_id):
            emsg = "Failed to create link " + self.link_id
            self.logger.error("[Link] HappyLinkAdd: %s" % (emsg))
            self.exit()

    def __add_new_link_state(self):
        new_link = {}
        new_link["node"] = None
        new_link["network"] = None
        new_link["type"] = self.type
        new_link["number"] = self.link_number
        new_link["node_end"] = self.link_node_end
        new_link["network_end"] = self.link_network_end
        new_link["tap"] = self.tap

        self.setLink(self.link_id, new_link)

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.link_number = self.__get_link_number()

            self.__get_link_id()

            self.__get_link_ends()

            self.__check_if_link_exists()

            self.__create_link()

            self.__turn_down_link_ends()

            self.__post_check()

            self.__add_new_link_state()

            self.writeState()

        return ReturnMsg(0, self.link_id)
