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

import happy.HappyLinkAdd
import happy.HappyLinkDelete
import happy.HappyLinkList


class test_happy_node_module(unittest.TestCase):
    def setUp(self):
        pass

    def test_node(self):
        options = happy.HappyLinkAdd.option()
        options["type"] = "thread"
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "wifi"
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "wan"
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "cellular"
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkList.option()
        options["quiet"] = True
        listLink = happy.HappyLinkList.HappyLinkList(options)
        listLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "thread0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "wifi0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "wan0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "cellular0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkList.option()
        options["quiet"] = True
        listLink = happy.HappyLinkList.HappyLinkList(options)
        listLink.run()

        # TAP

        options = happy.HappyLinkAdd.option()
        options["type"] = "thread"
        options["tap"] = True
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "wifi"
        options["tap"] = True
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "wan"
        options["tap"] = True
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkAdd.option()
        options["type"] = "cellular"
        options["tap"] = True
        options["quiet"] = True
        addLink = happy.HappyLinkAdd.HappyLinkAdd(options)
        addLink.run()

        options = happy.HappyLinkList.option()
        options["quiet"] = True
        listLink = happy.HappyLinkList.HappyLinkList(options)
        listLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "thread0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "wifi0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "wan0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkDelete.option()
        options["link_id"] = "cellular0"
        options["quiet"] = True
        deleteLink = happy.HappyLinkDelete.HappyLinkDelete(options)
        deleteLink.run()

        options = happy.HappyLinkList.option()
        options["quiet"] = True
        listLink = happy.HappyLinkList.HappyLinkList(options)
        listLink.run()

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
