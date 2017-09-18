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
#       Implements HappyNodeTcpReset class through which nodes reset tcp connection on specific interface
#
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
import happy.HappyProcessStart

options = {}
options["quiet"] = False
options["node_id"] = None
options["action"] = None
options["interface"] = None
options["start"] = None
options["duration"] = None
options["ips"] = None
options["dstPort"] = None


def option():
    return options.copy()


class HappyNodeTcpReset(HappyNode):
    """
    happy-node-tcp-reset provides tcpkill functionality to virtual nodes.

    happy-node-tcp-reset [-h --help] [-q --quiet] [-s --start [start_time]] [-d --duration [duration]]
                         [-i --ips [source ip, dest ip]] [-i --id <NODE_NAME>] [-d --dstPort <dstPort>]

    Example:
    $  happy-node-tcp-reset  --id BorderRouter --interface "wlan0"  --ips "107.22.61.55,10.0.1.2" --start "2" --duration 6
    #  happy-node-tcp-reset --id BorderRouter --interface "wlan0"  --dstPort "11095" --start "2" --duration "20"

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]

        self.action = opts["action"]
        self.interface = opts["interface"]
        self.begin = opts["start"]
        self.duration = opts["duration"]
        self.ips = opts["ips"]
        self.dstPort = opts["dstPort"]

    def __pre_check(self):
        # Check if the name of the node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should join a network."
            self.logger.error("[localhost] HappyNodeJoin: %s" % (emsg))
            self.exit()

        # Check if node exists
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyNodeJoin: %s" % (self.node_id, emsg))
            self.exit()

    def start_process(self, node_id, cmd, tag, quiet=None, strace=True):
        emsg = "start_weave_process %s at %s node." % (tag, node_id)
        self.logger.debug("[%s] process: %s" % (node_id, emsg))
        options = happy.HappyProcessStart.option()
        options["quiet"] = self.quiet
        options["node_id"] = node_id
        options["tag"] = tag
        options["command"] = cmd
        options["strace"] = True

        proc = happy.HappyProcessStart.HappyProcessStart(options)
        proc.run()

    def __TcpResetConnection(self):
        path = os.path.dirname(os.path.abspath(__file__))
        cmd = "python " + path + "/HappyPacketProcess.py --interface %s --start %d --duration %d --action RESET " % \
              (self.interface, self.begin, self.duration)
        if self.ips is not None:
            cmd += " --ips %s" % self.ips
        if self.dstPort is not None:
            cmd += " --dstPort %d" % self.dstPort
        if self.quiet is True:
            cmd += " --quiet"
        cmd = self.runAsRoot(cmd)
        self.start_process(node_id=self.node_id, cmd=cmd, tag="TcpReset")

    def run(self):
        self.__pre_check()
        self.__TcpResetConnection()
        return ReturnMsg(0)
