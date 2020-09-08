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
#       Implements HappyNetworkDelete class that removes virtual networks.
#
#       A virtual network is logical representation of a virtual ethernet
#       bridge, thus deleting a virtual network corresponds to deleting a bridge.
#

from __future__ import absolute_import
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNetwork import HappyNetwork
import happy.HappyLinkDelete
import happy.HappyNetworkState

options = {}
options["quiet"] = False
options["network_id"] = None


def option():
    return options.copy()


class HappyNetworkDelete(HappyNetwork):
    """
    Deletes a virtual network. A virtual network is logical representation
    of a virtual ethernet bridge, thus deleting a virtual network corresponds
    to deleting a bridge. If the network has any interfaces, those interfaces
    will be deleted as well.

    happy-network-delete [-h --help] [-q --quiet] [-i --id <NETWORK_NAME>]

        -i --id     Required. Network to delete. Find using happy-network-list
                    or happy-state.

    Example:
    $ happy-network-delete HomeThread
        Deletes the HomeThread network.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)

        self.quiet = opts["quiet"]
        self.network_id = opts["network_id"]
        self.done = False

    def __pre_check(self):
        # Check if the name of the new network is given
        if not self.network_id:
            emsg = "Missing name of the new virtual network that should be deleted."
            self.logger.error("[localhost] HappyNetworkAdd: %s" % (emsg))
            self.exit()

        if not self._networkExists():
            emsg = "virtual network %s does not exist." % (self.network_id)
            self.logger.warning("[%s] HappyNetworkDelete: %s" % (self.network_id, emsg))
            self.done = True

    def __delete_network(self):
        cmd = "brctl delbr " + self.uniquePrefix(self.network_id)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(self.network_id, cmd)

        cmd = "ip netns del " + self.uniquePrefix(self.network_id)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __post_check(self):
        if self._networkExists():
            emsg = "Failed to delete virtual network %s." % (self.network_id)
            self.logger.error("[%s] HappyNetworkDelete: %s" % (self.network_id, emsg))
            self.exit()

    def __network_down(self):
        options = happy.HappyNetworkState.option()
        options["network_id"] = self.network_id
        options["quiet"] = self.quiet
        options["down"] = True

        down_network = happy.HappyNetworkState.HappyNetworkState(options)
        down_network.run()

        self.readState()

    def __delete_network_state(self):
        self.removeNetwork(self.network_id)

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            if not self.done:
                self.__network_down()

                self._delete_network_interfaces()
                self.readState()

                self.__delete_network()

            self.__post_check()

            self.__delete_network_state()

            self.writeState()

        return ReturnMsg(0)
