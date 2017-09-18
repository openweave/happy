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
#       Tests happy process starting, stopping, waiting, getting output.
#

import pexpect
import os
import time
import unittest


class test_happy_process_shell(unittest.TestCase):

    def setUp(self):
        pass

    def test_node(self):
        os.system("happy-node-add node01")
        os.system("happy-process-start node01 PING-TEST ping -c 1 127.0.0.1")
        time.sleep(1.1)
        os.system("happy-process-start -i node01 -t PING-TEST ping -c 1 127.0.0.1")
        time.sleep(1.1)

        child = pexpect.spawn("happy-process-output node01 PING-TEST")
        child.expect('1 packets transmitted, 1 received')
        child.close(force=True)

        os.system("happy-node-delete node01")

        child = pexpect.spawn("happy-state")
        child.expect('   Prefixes\r\n\r\nNODES      Name    Interface    Type                                          IPs\r\n\r\n')
        child.close(force=True)

    def tearDown(self):
        os.system("happy-state-delete")

if __name__ == "__main__":
    unittest.main()
