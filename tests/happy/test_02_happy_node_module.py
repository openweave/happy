#!/usr/bin/env python

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
#       Tests happy for creating, deleting, and listing nodes.
#

import pexpect
import os
import unittest

import happy.HappyNodeAdd
import happy.HappyNodeDelete
import happy.HappyNodeList
import happy.HappyNodeStatus


class test_happy_node_module(unittest.TestCase):
    def setUp(self):
        pass

    def test_node(self):
        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node01"
        options["quiet"] = True
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node02"
        options["quiet"] = True
        options["type"] = "ap"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node03"
        options["quiet"] = True
        options["type"] = "service"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeAdd.option()
        options["node_id"] = "node04"
        options["quiet"] = True
        options["type"] = "local"
        addNode = happy.HappyNodeAdd.HappyNodeAdd(options)
        addNode.run()

        options = happy.HappyNodeList.option()
        options["quiet"] = True
        listNode = happy.HappyNodeList.HappyNodeList(options)
        listNode.run()

        options = happy.HappyNodeStatus.option()
        options["quiet"] = True
        statusNode = happy.HappyNodeStatus.HappyNodeStatus(options)
        statusNode.run()

        options = happy.HappyNodeStatus.option()
        options["node_id"] = "node01"
        options["quiet"] = True
        statusNode = happy.HappyNodeStatus.HappyNodeStatus(options)
        statusNode.run()

        options = happy.HappyNodeStatus.option()
        options["node_id"] = "node02"
        options["quiet"] = True
        statusNode = happy.HappyNodeStatus.HappyNodeStatus(options)
        statusNode.run()

        options = happy.HappyNodeStatus.option()
        options["node_id"] = "node03"
        options["quiet"] = True
        statusNode = happy.HappyNodeStatus.HappyNodeStatus(options)
        statusNode.run()

        options = happy.HappyNodeStatus.option()
        options["node_id"] = "node04"
        options["quiet"] = True
        statusNode = happy.HappyNodeStatus.HappyNodeStatus(options)
        statusNode.run()

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

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
