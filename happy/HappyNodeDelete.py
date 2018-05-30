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
#       Implements HappyNodeDelete class that removes virtual nodes.
#
#       A virtual node is logical representation of a network namespace, thus
#       deleting a virtual node corresponds to deleting a network namespace.
#

import os
import sys
import pprint

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
import happy.HappyProcessStop
import happy.HappyNodeTmux

options = {}
options["quiet"] = False
options["node_id"] = None


def option():
    return options.copy()


class HappyNodeDelete(HappyNode):
    """
    Deletes a virtual node. All network interfaces associated with the node
    are also deleted.

    happy-node-delete [-h --help] [-q --quiet] [-i --id <NODE_NAME>]

        -i --id     Required. Name of the node to delete.

    Example:
    $ happy-node-delete ThreadNode
        Deletes the ThreadNode node and all its associated interfaces.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.done = False

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the new virtual node that should be deleted."
            self.logger.error("[localhost] HappyNodeDelete: %s" % (emsg))
            self.exit()

        if not self._nodeExists() and self.node_id not in self.getNodeIds():
            emsg = "virtual node %s does not exist" % (self.node_id)
            self.logger.warning("[%s] HappyNodeDelete: %s" % (self.node_id, emsg))
            self.done = True

    def __stop_node_processes(self):
        tags = self.getNodeProcessIds()
        for tag in tags:
            options = happy.HappyProcessStop.option()
            options["quiet"] = self.quiet
            options["node_id"] = self.node_id
            options["tag"] = tag

            try:
                procStop = happy.HappyProcessStop.HappyProcessStop(options)
                procStop.run()
            except Exception:
                pass

            self.readState()

    def __delete_node(self):
        if not self.isNodeLocal(self.node_id):
            cmd = "ip netns del " + self.uniquePrefix(self.node_id)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

    def __post_check(self):
        if not self.isNodeLocal() and self._nodeExists():
            emsg = "Failed to delete virtual node %s." % (self.node_id)
            self.logger.error("[%s] HappyNodeDelete: %s" % (self.node_id, emsg))
            self.exit()

    def __delete_node_state(self):
        self.removeNode(self.node_id)

    def __delete_identifier_state(self):
        self.removeIdentifiersMap(self.node_id)

    def __delete_netns_state(self):
        self.removeNodeNetNsMap(self.node_id)

    def __delete_node_tmux_sessions(self):
        for session_id in self.getNodeTmuxSessionIds():

            options = happy.HappyNodeTmux.option()
            options["quiet"] = self.quiet
            options["node_id"] = self.node_id
            options["session"] = session_id
            options["delete"] = True

            delTmux = happy.HappyNodeTmux.HappyNodeTmux(options)
            delTmux.run()

            self.readState()

    def __delete_node_interfaces(self):

        self.DeleteNodeInterfaces()

        self.readState()

    def __delete_node_dir(self):
        nspath = self.nsroot + "/" + self.uniquePrefix(self.node_id)
        if os.path.isdir(nspath):
            cmd = "rm -r " + nspath
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            if not self.done:
                self.__stop_node_processes()

                self.__delete_node_interfaces()

                self.__delete_node_tmux_sessions()

                self.__delete_node()

            self.__post_check()

            self.__delete_node_state()

            self.__delete_node_dir()

            self.__delete_identifier_state()

            self.__delete_netns_state()

            self.writeState()

        return ReturnMsg(0)
