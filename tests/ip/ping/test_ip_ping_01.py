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
#       Calls ping between nodes.
#

from __future__ import absolute_import
from __future__ import print_function
import itertools
import os
import unittest

import happy.Ping
from happy.Utils import *

import happy.HappyNodeList
import happy.HappyStateLoad
import happy.HappyStateUnload


class test_ip_ping_02(unittest.TestCase):
    def setUp(self):
        self.topology_file = os.path.dirname(os.path.realpath(__file__)) + \
            "/../../../topologies/three_nodes_on_thread_weave.json"

        # setting Mesh for thread test
        options = happy.HappyStateLoad.option()
        options["quiet"] = True
        options["json_file"] = self.topology_file

        setup_network = happy.HappyStateLoad.HappyStateLoad(options)
        ret = setup_network.run()

    def tearDown(self):
        # cleaning up
        options = happy.HappyStateUnload.option()
        options["quiet"] = True
        options["json_file"] = self.topology_file

        teardown_network = happy.HappyStateUnload.HappyStateUnload(options)
        teardown_network.run()

    def __send_ping_between(self, nodeA, nodeB):
        options = happy.Ping.option()
        options["quiet"] = True    # False will show detailed ping results
        options["source"] = nodeA
        options["destination"] = nodeB
        options["count"] = "4"

        ping = happy.Ping.Ping(options)
        ret = ping.run()

        value = ret.Value()
        data = ret.Data()

        return value, data

    def test_ip_ping_among_all_nodes(self):
        options = happy.HappyNodeList.option()
        options["quiet"] = True

        nodes_list = happy.HappyNodeList.HappyNodeList(options)
        ret = nodes_list.run()

        node_ids = ret.Data()
        pairs_of_nodes = list(itertools.product(node_ids, node_ids))

        for pair in pairs_of_nodes:
            value, data = self.__send_ping_between(pair[0], pair[1])

            print("ping from " + pair[0] + " to " + pair[1] + " ", end=' ')

            if value > 11:
                print(hred("Failed"))
            else:
                print(hgreen("Passed"))

if __name__ == "__main__":
    unittest.main()
