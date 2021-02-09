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
import happy.HappyDNS

options = {}
options["quiet"] = False
options["node_id"] = None
options["new_node_id"] = None
options["type"] = None


def option():
    return options.copy()


class HappyNodeEdit(HappyNode):
    """
    Edit the state of an existing virtual node.  Example operations are rename.

    happy-node-edit [-h --help] [-q --quiet]
                    [-i --id <NODE_NAME>] [-n --new <NEW_NODE_NAME>]

        -i --id         Required. Name of the node to edit.
        -n --new        New name of the node for rename.

    Note: A node cannot be more than one type. It is either ap, service,
          or local.

    Examples:
    $ happy-node-edit -i node1 -n onhub 
        Renames node1 to now be called onhub.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.new_node_id = opts["new_node_id"]
        self.type = opts["type"]

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node to edit."
            self.logger.error("[localhost] HappyNodeEdit: %s" % (emsg))
            self.exit()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if not self._nodeExists():
            emsg = "virtual node %s does not exists." % (self.node_id)
            self.logger.warning("[%s] HappyNodeEdit: %s" % (self.node_id, emsg))

        # Check if dot is in the name
        if IP.isDomainName(self.new_node_id):
            emsg = "Using . (dot) in the name is not allowed."
            self.logger.error("[localhost] HappyNodeEdit: %s" % (emsg))
            self.exit()

    def __post_check(self):
        if not self._nodeExists(self.new_node_id):
            emsg = "Virtual node does not exist"
            self.logger.error("[%s] HappyNodeEdit: %s" % (self.node_id, emsg))
            self.exit()

    def __edit_node_state(self):
        if (self.new_node_id):
            self.logger.info("HappyNodeEdit: renaming node "+self.node_id+" to "+self.new_node_id)
            self.renameNode(self.node_id, self.new_node_id)

            # Update all link references
            links = self.getLinks()
            for key in links:
                if links[key]["node"] == self.node_id:
                    links[key]["node"] = self.new_node_id

            # Update identifiers references
            identifiers = self.getShortIdToLongIdMap()
            for value in identifiers.values():
                if value["id"] == self.node_id:
                    value["id"] = self.new_node_id

            # Update netns references
            netns_map = self.getNetNS()
            netns_map[self.new_node_id] = netns_map[self.node_id]
            del netns_map[self.node_id]

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.__edit_node_state()

            self.writeState()

            self.__post_check()

        return ReturnMsg(0)
