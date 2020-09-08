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
#       Tests happy for creating, deleting, and listing networks.
#

from __future__ import absolute_import
import pexpect
import os
import unittest


class test_happy_network_shell(unittest.TestCase):

    def setUp(self):
        pass

    def test_network(self):
        os.system("happy-network-add -t thread network01")
        os.system("happy-network-add --type wifi network02")
        os.system("happy-network-add -t wan network03")
        os.system("happy-network-add --t cellular network04")

        os.system("happy-network-list &> /dev/null")

        os.system("happy-network-status &> /dev/null")
        os.system("happy-network-status network01 &> /dev/null")
        os.system("happy-network-status network02 &> /dev/null")
        os.system("happy-network-status network03 &> /dev/null")
        os.system("happy-network-status network04 &> /dev/null")

        os.system("happy-network-delete network01")
        os.system("happy-network-delete network02")
        os.system("happy-network-delete network03")
        os.system("happy-network-delete network04")

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
