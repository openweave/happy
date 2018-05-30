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
#       Implements HappyProcessWait class that waits for a running process to stop.
#
#       Process runs a command in a virtual node, which itself
#       is a logical representation of a network namespace.
#

import os
import sys
import time

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
from happy.HappyProcess import HappyProcess

options = {}
options["quiet"] = False
options["node_id"] = None
options["tag"] = None
options["timeout"] = None


def option():
    return options.copy()


class HappyProcessWait(HappyNode, HappyProcess):
    """
    Waits for a process to finish execution on a virtual node.

    happy-process-wait [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                       [-t --tag <DAEMON_NAME>]

        -i --id     Required. Node on which the process is running. Find
                    using happy-node-list or happy-state.
        -t --tag    Required. Name of the process.

    Example:
    $ happy-process-wait ThreadNode QuickPing
        Prevents further Happy command execution on the ThreadNode node
        until the QuickPing process has completed execution.

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
        self.timeout = opts["timeout"]
        self.done = False

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should stop process."
            self.logger.error("[localhost] HappyProcessWait: %s" % (emsg))
            self.RaiseError()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyProcessWait: %s" % (self.node_id, emsg))
            self.RaiseError()

        # Check if the new process is given
        if not self.tag:
            emsg = "Missing name of the process to be stopped."
            self.logger.error("[%s] HappyProcessWait: %s" % (self.node_id, emsg))
            self.RaiseError()

        # Check if a process exists
        if not self.processExists(self.tag, self.node_id):
            self.done = True

    def run(self):
        self.__pre_check()

        if not self.done:
            emsg = "Waiting for process %s to complete." % (self.tag)
            self.logger.debug("[%s] HappyProcessWait: %s" % (self.node_id, emsg))

            self.BlockOnProcess(self.tag, self.node_id, self.timeout)
        else:
            emsg = "Process %s already completed." % (self.tag)
            self.logger.debug("[%s] HappyProcessWait: %s" % (self.node_id, emsg))

        return ReturnMsg(0)
