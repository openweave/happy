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
#       Implements HappyNetworkState class that shows virtual networks.
#

import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNetwork import HappyNetwork

options = {}
options["quiet"] = False
options["network_id"] = None
options["up"] = False
options["down"] = False


def option():
    return options.copy()


class HappyNetworkState(HappyNetwork):
    """
    Changes or displays the state of a virtual network's interfaces.

    happy-network-state [-h --help] [-q --quiet] [-u --up] [-d --down]
                        [-i --id <NETWORK_NAME>]

        -u --up     Bring up all interfaces on the specified network.
        -d --down   Bring down all interfaces on the specified network.
        -i --id     Required. Network to change or display the state of network
                    interfaces. Find using happy-network-list or happy-state.
    
    Examples:
    $ happy-network-state HomeThread
        Displays the current state of the HomeThread network.

    $ happy-network-state -d HomeThread
        Brings down all HomeThread network interfaces.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)

        self.quiet = opts["quiet"]
        self.network_id = opts["network_id"]
        self.up = opts["up"]
        self.down = opts["down"]

    def __pre_check(self):
        # Check if the name of the new network is given
        if not self.network_id:
            emsg = "Missing name of the new virtual network."
            self.logger.error("[localhost] HappyNetworkState: %s" % (emsg))
            self.exit()

        # Check if the virtual network exists
        if self.network_id is not None and not self._networkExists():
            emsg = "virtual network %s does not exist" % (self.network_id)
            self.logger.error("[%s] HappyNetworkState: %s" % (self.network_id, emsg))
            self.exit()

    def __network_up(self):
        cmd = "ifconfig " + self.uniquePrefix(self.network_id) + " up"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNetwork(self.network_id, cmd)

    def __network_down(self):
        cmd = "ifconfig " + self.uniquePrefix(self.network_id) + " down"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNetwork(self.network_id, cmd)

    def __update_network_state(self):
        if self.network_id not in self.getNetworkIds():
            return

        if self.up:
            self.setNetworkState(self.network_id, "UP")

        if self.down:
            self.setNetworkState(self.network_id, "DOWN")

    def __post_check(self):
        if not self.up and not self.down:
            return True

        new_state = self._networkState()
        if new_state != "UP" and new_state != "DOWN":
            return True

        if self.up and new_state != "UP":
            emsg = "Failed to bring virtual network %s UP." % (self.network_id)
            self.logger.error("[%s] HappyNetworkState: %s" % (self.network_id, emsg))
            self.exit()

        if self.down and new_state != "DOWN":
            emsg = "Failed to bring virtual network %s DOWN." % (self.network_id)
            self.logger.error("[%s] HappyNetworkState: %s" % (self.network_id, emsg))
            self.exit()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            if self.up:
                self.__network_up()

            if self.down:
                self.__network_down()

            self.__post_check()

            if not self.up and not self.down:
                state = self._networkState()
                print "Network " + self.network_id + ": " + state

            else:
                self.__update_network_state()
                self.writeState()

        return ReturnMsg(0)
