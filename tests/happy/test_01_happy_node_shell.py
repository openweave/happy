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
#       Tests happy for creating, deleting, and listing nodes.
#

from __future__ import absolute_import
import pexpect
import os
import unittest


class test_happy_node_shell(unittest.TestCase):
    def setUp(self):
        pass

    def test_node(self):
        os.system("happy-node-add node01")
        os.system("happy-node-add -i node02")
        os.system("happy-node-add --id node03")
        os.system("happy-node-add -a node04")
        os.system("happy-node-add --ap node05")
        os.system("happy-node-add -s node06")
        os.system("happy-node-add --service node07")
        os.system("happy-node-add -l node08")
        os.system("happy-node-add --local node09")

        os.system("happy-node-list &> /dev/null")

        os.system("happy-node-status &> /dev/null")
        os.system("happy-node-status node01 &> /dev/null")
        os.system("happy-node-status node02 &> /dev/null")
        os.system("happy-node-status node03 &> /dev/null")
        os.system("happy-node-status node04 &> /dev/null")
        os.system("happy-node-status node05 &> /dev/null")
        os.system("happy-node-status node06 &> /dev/null")
        os.system("happy-node-status node07 &> /dev/null")
        os.system("happy-node-status node08 &> /dev/null")
        os.system("happy-node-status node09 &> /dev/null")

        os.system("happy-node-delete node01")
        os.system("happy-node-delete node02")
        os.system("happy-node-delete node03")
        os.system("happy-node-delete node04")
        os.system("happy-node-delete node05")
        os.system("happy-node-delete node06")
        os.system("happy-node-delete node07")
        os.system("happy-node-delete node08")
        os.system("happy-node-delete node09")

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
