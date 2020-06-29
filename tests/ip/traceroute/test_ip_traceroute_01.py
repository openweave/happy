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
#       Calls traceroute between nodes.
#

from __future__ import absolute_import
import os
import unittest

import happy.HappyStateLoad
import happy.HappyStateUnload
import happy.Traceroute


class test_ip_traceroute_01(unittest.TestCase):
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

    def test_ip_traceroute(self):
        # Simple traceroute betwenn node00 and node01
        options = happy.Traceroute.option()
        options["quiet"] = False
        options["source"] = "node01"
        options["destination"] = "node02"

        traceroute = happy.Traceroute.Traceroute(options)
        ret = traceroute.run()

        value = ret.Value()
        data = ret.Data()

        self.assertTrue(value < 11, "%s < 11 %%" % (str(value)))

if __name__ == "__main__":
    unittest.main()
