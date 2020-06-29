#!/usr/bin/env python3

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
#       Tests happy node joining and leaving a network.
#

from __future__ import absolute_import
import pexpect
import os
import unittest

import happy.HappyNetworkAdd
import happy.HappyNetworkDelete
import happy.HappyNodeAdd
import happy.HappyNodeDelete
import happy.HappyNodeJoin
import happy.HappyNodeLeave


class test_happy_node_network_module(unittest.TestCase):
    def setUp(self):
        pass

    def test_node(self):
        options = happy.HappyNodeAdd.option()
        options["quiet"] = True
        options["node_id"] = "node01"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNetworkAdd.option()
        options["quiet"] = True
        options["network_id"] = "network01"
        options["type"] = "thread"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node01"
        options["network_id"] = "network01"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeAdd.option()
        options["quiet"] = True
        options["node_id"] = "node02"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNetworkAdd.option()
        options["quiet"] = True
        options["network_id"] = "network02"
        options["type"] = "wifi"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node02"
        options["network_id"] = "network02"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node01"
        options["network_id"] = "network02"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node03"
        options["quiet"] = True
        options["type"] = "ap"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node04"
        options["quiet"] = True
        options["type"] = "service"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node05"
        options["quiet"] = True
        options["type"] = "local"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node06"
        options["quiet"] = True
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNetworkAdd.option()
        options["quiet"] = True
        options["network_id"] = "network03"
        options["type"] = "wan"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node03"
        options["network_id"] = "network03"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node04"
        options["network_id"] = "network03"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node05"
        options["network_id"] = "network03"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeJoin.option()
        options["quiet"] = True
        options["node_id"] = "node06"
        options["network_id"] = "network03"
        joinNetwork = happy.HappyNodeJoin.HappyNodeJoin(options)
        joinNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node01"
        options["network_id"] = "network01"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node02"
        options["network_id"] = "network02"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node01"
        options["network_id"] = "network02"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node03"
        options["network_id"] = "network03"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node04"
        options["network_id"] = "network03"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node05"
        options["network_id"] = "network03"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeLeave.option()
        options["quiet"] = True
        options["node_id"] = "node06"
        options["network_id"] = "network03"
        leaveNetwork = happy.HappyNodeLeave.HappyNodeLeave(options)
        leaveNetwork.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node01"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node02"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node03"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node04"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node05"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNodeDelete.option()
        options["node_id"] = "node06"
        options["quiet"] = True
        delNode = happy.HappyNodeDelete.HappyNodeDelete(options)
        delNode.run()

        options = happy.HappyNetworkDelete.option()
        options["network_id"] = "network01"
        options["quiet"] = True
        delNetwork = happy.HappyNetworkDelete.HappyNetworkDelete(options)
        delNetwork.run()

        options = happy.HappyNetworkDelete.option()
        options["network_id"] = "network02"
        options["quiet"] = True
        delNetwork = happy.HappyNetworkDelete.HappyNetworkDelete(options)
        delNetwork.run()

        options = happy.HappyNetworkDelete.option()
        options["network_id"] = "network03"
        options["quiet"] = True
        delNetwork = happy.HappyNetworkDelete.HappyNetworkDelete(options)
        delNetwork.run()

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
