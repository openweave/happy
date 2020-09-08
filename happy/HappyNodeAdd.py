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
#       Implements HappyNodeAdd class that creates virtual nodes.
#
#       A virtual node is logical representation of a network namespace.
#

from __future__ import absolute_import
import os
import sys
import time

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.utils.IP import IP
from happy.HappyNode import HappyNode
import happy.HappyNodeDelete
import happy.HappyDNS

options = {}
options["quiet"] = False
options["node_id"] = None
options["type"] = None


def option():
    return options.copy()


class HappyNodeAdd(HappyNode):
    """
    Creates a new network namespace that represents one virtual node.

    happy-node-add [-h --help] [-q --quiet] [-a --ap] [-s --service]
                   [-l --local] [-i --id <NODE_NAME>]

        -a --ap         The node is considered an access point.
        -s --service    The node is considered a cloud service.
        -l --local      Default node type. The node is considered a local node.
        -i --id         Required. Name of the node to create.

    Note: A node cannot be more than one type. It is either ap, service,
          or local.

    Examples:
    $ happy-node-add onhub
        Creates a node called onhub.

    $ happy-node-add --ap --id onhub
        Creates a node called onhub that serves as an access point.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.type = opts["type"]

    def __deleteExistingNode(self):
        options = happy.HappyNodeDelete.option()
        options["node_id"] = self.node_id
        options["quiet"] = self.quiet
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        self.readState()

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the new virtual node that should be created."
            self.logger.error("[localhost] HappyNodeAdd: %s" % (emsg))
            self.exit()

        # Check if dot is in the name
        if IP.isDomainName(self.node_id):
            emsg = "Using . (dot) in the name is not allowed."
            self.logger.error("[localhost] HappyNodeAdd: %s" % (emsg))
            self.exit()

        # Check if node type is valid
        if self.type is not None and self.type not in self.node_special_type:
            emsg = "Unknown node type %s." % (self.type)
            self.logger.error("[localhost] HappyNodeAdd: %s" % (emsg))
            self.exit()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if self._nodeExists():
            emsg = "virtual node %s already exists." % (self.node_id)
            self.logger.warning("[%s] HappyNodeAdd: %s" % (self.node_id, emsg))
            self.__deleteExistingNode()

        # Check if there is some old record of a node
        if self.node_id in self.getNodeIds():
            self.__deleteExistingNode()

    def __create_node(self):
        if self.type != self.node_type_local:
            cmd = "ip netns add " + self.uniquePrefix(self.node_id)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

    def __post_check(self):
        if self.type != self.node_type_local and not self._nodeExists():
            emsg = "Failed to create virtual node"
            self.logger.error("[%s] HappyNodeAdd: %s" % (self.node_id, emsg))
            self.exit()

    def __add_new_node_state(self):
        new_node = {}
        new_node["type"] = self.type
        new_node["interface"] = {}
        new_node["route"] = {}
        new_node["tmux"] = {}
        new_node["process"] = {}

        self.setNode(self.node_id, new_node)

    def __bring_loopback(self):
        if self.type != self.node_type_local:
            cmd = "ifconfig lo up"
            r = self.CallAtNode(self.node_id, cmd)

    def __check_node_type(self):
        if self.type == self.node_type_ap:
            self.nodeIPv6Forwarding(1, self.node_id)
            self.nodeIPv4Forwarding(1, self.node_id)

        if self.type == self.node_type_service:
            pass

        if self.type == self.node_type_local:
            pass

    def __check_for_dns(self):
        dns = self.getDNS()
        if dns is not None:
            options = happy.HappyDNS.option()
            options["node_id"] = self.node_id
            options["quiet"] = self.quiet
            options["add"] = True
            options["dns"] = dns
            nodeDNS = happy.HappyDNS.HappyDNS(options)
            nodeDNS.run()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.__add_new_node_state()

            # write the state before creating the node,
            # otherwise if we get a SIGTERM between creating the
            # namespace and writing the state file, the network
            # namespace is leaked
            self.writeState()

            self.__create_node()

            self.__post_check()

            self.__bring_loopback()

            self.__check_node_type()

            self.__check_for_dns()

        return ReturnMsg(0)
