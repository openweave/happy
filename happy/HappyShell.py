#!/usr/bin/env python3

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
#       Implements HappyNodeAdd class that creates virtual nodes.
#
#       A virtual node is logical representation of a network namespace.
#

from __future__ import absolute_import
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["node_id"] = None
options["run_as_user"] = False
options["command"] = None


def option():
    return options.copy()


class HappyShell(HappyNode):
    """
    Logs the user into a virtual node so commands can be run directly in the node,
    or runs commands as if the user is currently logged into the node.

    happy-shell [-h --help] [-q --quiet] [-i --id <NODE_NAME>] [-u --user]
                [-c --command <COMMAND>]

        -i --id         Required. Node to log into. Find using happy-node-list or
                        happy-state.
        -u --user       Optional. User to log into the node as.
        -c --command    Optional. Run <COMMAND> in the node and view its output
                        without directly logging in.

    Examples:
    $ happy-shell BorderRouter
        Log into the BorderRouter node.

    $ happy-shell BorderRouter ping -c2 10.0.1.3
        Pings 10.0.1.3 twice from within the BorderRouter node and outputs the
        results.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.run_as_user = opts["run_as_user"]
        self.command = opts["command"]
        self.result = None

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should start shell."
            self.logger.error("[%s] HappyShell: %s" % (self.node_id, emsg))
            self.exit()

        # Check if virtual node exists
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyShell: %s" % (self.node_id, emsg))
            self.exit()

    def __post_check(self):
        pass

    def run(self):
        self.__pre_check()

        cmd = ""

        if self.run_as_user:
            try:
                user = os.environ['USER']
                cmd = self.runAsUser(cmd, user)
            except Exception:
                pass

        env = os.environ

        env["PS1"] = r'\u@' + '\[\e[1;32m\]' + self.node_id + '\[\e[m\]' + ':\w\$ '
        env["HAPPY_HOST"] = self.node_id

        if self.command:
            cmd += self.command
        else:
            cmd += 'bash --norc'

        self.result = self.CallAtNode(self.node_id, cmd, env, output='shell')

        self.__post_check()

        return ReturnMsg(0)
