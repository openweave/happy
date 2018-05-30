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
#       Implements HappyLinkDelete class that removes virtual nodes.
#
#       A virtual node is logical representation of a network namespace, thus
#       deleting a virtual link corresponds to deleting a network namespace.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyLink import HappyLink

options = {}
options["quiet"] = False
options["link_id"] = None


def option():
    return options.copy()


class HappyLinkDelete(HappyLink):
    """
    Deletes a virtual link. A virtual link is logical representation of a
    network interface.

    happy-link-delete [-h --help] [-q --quiet] [-i --id <LINK_NAME>]

        -i --id     Required. Link to delete. Find using happy-link-list.

    Example:
    $ happy-link-delete wifi0
        Deletes the wifi0 network link.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyLink.__init__(self)

        self.quiet = opts["quiet"]
        self.link_id = opts["link_id"]
        self.done = False

    def __pre_check(self):
        # Check if the name of the new link is given
        if not self.link_id:
            emsg = "Missing name of the new virtual link that should be deleted."
            self.logger.error("[%s] HappyLinkDelete: %s" % (self.link_id, emsg))
            self.exit()

        if not self._linkExists():
            emsg = "virtual link %s does not exist." % (self.link_id)
            self.logger.warning("[%s] HappyLinkDelete: %s" % (self.link_id, emsg))
            self.done = True

    def __delete_link(self):
        if self.link_id in self.getLinkIds():
            network_id = self.getLinkNetwork(self.link_id)
            node_id = self.getLinkNode(self.link_id)

            cmd = "ip link delete " + self.getLinkNetworkEnd(self.link_id)
            cmd = self.runAsRoot(cmd)

            if network_id:
                ret = self.CallAtNetwork(network_id, cmd)
            else:
                ret = self.CallAtHost(cmd)

            if self.getLinkTap(self.link_id):
                cmd = "ip link delete " + self.getTapBridgeId(self.link_id)
                cmd = self.runAsRoot(cmd)

                if node_id:
                    ret = self.CallAtNode(node_id, cmd)
                else:
                    ret = self.CallAtHost(cmd)

                if node_id:
                    interface_id = self.getNodeInterfaceFromLink(self.link_id, node_id)
                    cmd = "ip link delete " + interface_id
                    cmd = self.runAsRoot(cmd)
                    ret = self.CallAtNode(node_id, cmd)
                else:
                    cmd = "ip link delete " + self.getLinkNodeEnd(self.link_id)
                    cmd = self.runAsRoot(cmd)
                    ret = self.CallAtHost(cmd)

        else:
            cmd = ""
            host_links = self.getHostInterfaces()

            link_id = self.uniquePrefix(self.link_id)
            link_id_node = self.getUniqueLinkNodeEnd()

            if link_id in host_links:
                cmd = "ip link delete " + link_id

            if link_id_node in host_links:
                cmd = "ip link delete " + link_id_node

            if cmd != "":
                cmd = self.runAsRoot(cmd)
                ret = self.CallAtHost(cmd)

        return ret

    def __post_check(self):
        if self._linkExists():
            emsg = "Failed to delete virtual link %s" % (self.link_id)
            self.logger.error("[%s] HappyLinkDelete: %s" % (self.link_id, emsg))
            self.exit()

    def __delete_link_state(self):
        self.removeLink(self.link_id)

    def __delete_link_from_nodes(self):
        for node_id in self.getNodeIds():
            for interface_id in self.getNodeInterfaceIds(node_id):
                link_id = self.getNodeInterfaceLinkId(interface_id, node_id)
                if link_id == self.link_id:
                    self.removeNodeInterface(node_id, interface_id)

    def __delete_link_from_networks(self):
        for network_id in self.getNetworkIds():
            for link_id in self.getNetworkLinkIds(network_id):
                if link_id == self.link_id:
                    self.removeNetworkLink(network_id, link_id)

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            if not self.done:
                self.__delete_link()

            self.__post_check()

            self.__delete_link_from_nodes()
            self.__delete_link_from_networks()
            self.__delete_link_state()

            self.writeState()

        return ReturnMsg(0)
