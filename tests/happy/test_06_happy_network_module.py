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
#       Tests happy for creating, deleting, and listing networks.
#

import pexpect
import os
import unittest

import happy.HappyNetworkAdd
import happy.HappyNetworkDelete
import happy.HappyNetworkList
import happy.HappyNetworkStatus


class test_happy_network_module(unittest.TestCase):
    def setUp(self):
        pass

    def test_network(self):
        options = happy.HappyNetworkAdd.option()
        options["network_id"] = "network01"
        options["quiet"] = True
        options["type"] = "thread"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNetworkAdd.option()
        options["network_id"] = "network02"
        options["quiet"] = True
        options["type"] = "wifi"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNetworkAdd.option()
        options["network_id"] = "network03"
        options["quiet"] = True
        options["type"] = "wan"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNetworkAdd.option()
        options["network_id"] = "network04"
        options["quiet"] = True
        options["type"] = "cellular"
        addNetwork = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        addNetwork.run()

        options = happy.HappyNetworkList.option()
        options["quiet"] = True
        listNetwork = happy.HappyNetworkList.HappyNetworkList(options)
        listNetwork.run()

        options = happy.HappyNetworkStatus.option()
        options["quiet"] = True
        statusNetwork = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        statusNetwork.run()

        options = happy.HappyNetworkStatus.option()
        options["network_id"] = "network01"
        options["quiet"] = True
        statusNetwork = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        statusNetwork.run()

        options = happy.HappyNetworkStatus.option()
        options["network_id"] = "network02"
        options["quiet"] = True
        statusNetwork = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        statusNetwork.run()

        options = happy.HappyNetworkStatus.option()
        options["network_id"] = "network03"
        options["quiet"] = True
        statusNetwork = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        statusNetwork.run()

        options = happy.HappyNetworkStatus.option()
        options["network_id"] = "network04"
        options["quiet"] = True
        statusNetwork = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        statusNetwork.run()

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

        options = happy.HappyNetworkDelete.option()
        options["network_id"] = "network04"
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
