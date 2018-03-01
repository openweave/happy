#!/usr/bin/env python

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
#       Implements HappyProcessStop class that stops processes running within virtual nodes.
#
#       Process runs a command in a virtual node, which itself
#       is a logical representation of a network namespace.
#

import getpass
import os
import sys
import psutil

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
from happy.HappyProcess import HappyProcess

options = {}
options["quiet"] = False
options["node_id"] = None
options["tag"] = None


def option():
    return options.copy()


class HappyProcessStop(HappyNode, HappyProcess):
    """
    Stops a process that is running in a virtual node.

    happy-process-stop [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                       [-t --tag <DAEMON_NAME>]

        -i --id     Optional. Node on which the process is running. Find
                    using happy-node-list or happy-state.
        -t --tag    Required. Name of the process.

    Example:
    $ happy-process-stop ThreadNode ContinuousPing
        Stops execution of the ContinuousPing process on the ThreadNode
        node.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)
        HappyProcess.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.tag = opts["tag"]
        self.pid = None
        self.create_time = None
        self.process_exists = True

    def __pre_check(self):
        # Check if the tag is given
        if not self.tag:
            emsg = "Missing name of the process to be stopped."
            self.logger.error("[localhost] HappyProcessStop: %s" % (emsg))
            self.RaiseError()

        # Check if the process is still running.
        if not self.processExists(self.tag, self.node_id):
            emsg = "virtual process %s is no longer running." % (self.tag)
            self.logger.debug("[%s] HappyProcessStop: %s" % (self.node_id, emsg))
            self.process_exists = False

    def __stop_process(self):
        self.pid = self.getNodeProcessPID(self.tag, self.node_id)
        self.create_time = self.getNodeProcessCreateTime(self.tag, self.node_id)

        emsg = "Process %s has PID %s." % (self.tag, str(self.pid))
        self.logger.debug("[%s] HappyProcessStop: %s" % (self.node_id, emsg))

        self.TerminateProcessTree(self.pid, self.create_time)

    def __post_check(self):
        pass

    def run(self):
        self.__pre_check()

        if self.process_exists:
            self.__stop_process()

        self.__post_check()

        return ReturnMsg(0)
