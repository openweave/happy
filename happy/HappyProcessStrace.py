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
#       Implements HappyProcessStrace class that returns an strace of
#       a process running within virtual node.
#
#       Process runs a command in a virtual node, which itself
#       is a logical representation of a network namespace.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["node_id"] = None
options["tag"] = None


def option():
    return options.copy()


class HappyProcessStrace(HappyNode):
    """
    happy-process-strace  returns a process strace.

    happy-process-strace [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
        [-t --tag <DAEMON_NAME>]

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.tag = opts["tag"]
        self.process_strace = None

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node."
            self.logger.error("[localhost] HappyProcessStrace: %s" % (emsg))
            self.RaiseError()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyProcessStrace: %s" % (self.node_id, emsg))
            self.RaiseError()

        # Check if the new process is given
        if not self.tag:
            emsg = "Missing name of the process to retrieve strace from."
            self.logger.error("[localhost] HappyProcessStrace: %s" % (emsg))
            self.RaiseError()

    def __process_strace(self):
        fout = self.getNodeProcessStraceFile(self.tag, self.node_id)

        if not os.path.exists(fout):
            # Delay read in case of race condition
            delayExecution(0.5)

        try:
            with open(fout, 'r') as pout:
                self.process_strace = pout.read()

        except IOError as e:
            emsg = "Problem with %s: " % (fout)
            emsg += "I/O error({0}): {1}".format(e.errno, e.strerror)
            self.logger.error("[localhost] HappyProcessStrace: %s" % emsg)
            self.RaiseError(fout + ": " + e.strerror)

        except Exception:
            emsg = "Failed to open process strace file: %s." % (fout)
            self.logger.error("[localhost] HappyProcessStrace: %s" % emsg)
            self.RaiseError(emsg)

    def run(self):
        self.__pre_check()

        self.__process_strace()

        return ReturnMsg(0, self.process_strace)
