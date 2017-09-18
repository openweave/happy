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
#       Tests happy node joining and leaving a network.
#

import pexpect
import os
import unittest


class test_happy_node_network_shell(unittest.TestCase):
    def setUp(self):
        pass

    def test_node(self):
        os.system("happy-link-add thread")
        os.system("happy-link-add wifi")
        os.system("happy-link-add wan")
        os.system("happy-link-add cellular")

        os.system("happy-link-list --quiet")

        os.system("happy-link-delete thread0")
        os.system("happy-link-delete wifi0")
        os.system("happy-link-delete wan0")
        os.system("happy-link-delete cellular0")

        # TAP

        os.system("happy-link-add --tap thread")
        os.system("happy-link-add --tap wifi")
        os.system("happy-link-add --tap wan")
        os.system("happy-link-add --tap cellular")

        os.system("happy-link-list --quiet")

        os.system("happy-link-delete thread0")
        os.system("happy-link-delete wifi0")
        os.system("happy-link-delete wan0")
        os.system("happy-link-delete cellular0")

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
