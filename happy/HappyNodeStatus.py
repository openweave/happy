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
#       Implements HappyNodeStatus class that shows virtual nodes.
#

import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["node_id"] = None


def option():
    return options.copy()


class HappyNodeStatus(HappyNode):
    """
    Displays virtual node information.

    happy-node-status [-h --help] [-q --quiet] [-i --id <NODE_NAME>]

        -i --id     Node to display information for. Find using
                    happy-node-list or happy-state.

    Examples:
    $ happy-node-status
        Displays information for all nodes.

    $ happy-node-status ThreadNode
        Displays information for the ThreadNode node in JSON format.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]

    def __pre_check(self):
        # Check if the virtual node exists
        if self.node_id is not None and not self._nodeExists():
            emsg = "virtual node %s does not exist" % (self.node_id)
            self.logger.error("[%s] HappyNodeStatus: %s" % (self.node_id, emsg))
            self.exit()

    def __post_check(self):
        pass

    def __print_all_nodes(self):
        print "{0: >15} {1: >12} {2: >7} {3: >44}".format("NODES      Name", "Interface", "Type", "IPs")

        for node_id in self.getNodeIds():
            print "{0: >15}".format(node_id),

            interfaces = self.getNodeInterfaceIds(node_id)

            if len(interfaces) == 0:
                print
                continue

            for i in range(len(interfaces)):
                if i > 0:
                    print " " * 15,

                print "{0: >12} {1: >7}".format(interfaces[i],
                                                self.getNodeInterfaceType(interfaces[i], node_id)),

                addresses = self.getNodeInterfaceAddresses(interfaces[i], node_id)

                if len(addresses) == 0:
                    print
                    continue

                for a in range(len(addresses)):
                    if a > 0:
                        print " " * 36,

                    print " {0: >40}/{1: <3}".format(addresses[a],
                                                     self.getNodeInterfaceAddressMask(interfaces[i],
                                                     addresses[a], node_id))
                print

    def run(self):
        self.__pre_check()

        if self.node_id is None:
            self.__print_all_nodes()
            return 0

        data_state = json.dumps(self.getNode(self.node_id), sort_keys=True, indent=4)
        emsg = "virtual node state: " + self.node_id

        print emsg

        self.logger.info("[%s] HappyNodeStatus: %s" % (self.node_id, emsg))

        print data_state

        for line in data_state.split("\n"):
            if line is None or len(line) == 0:
                continue

            self.logger.info("[%s] HappyNodeStatus: %s" % (self.node_id, line))

        self.__post_check()

        return ReturnMsg(0)
