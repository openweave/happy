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
#       Implements HappyNetworkAdd class that creates virtual networks.
#
#       A virtual network is logical representation of a virtual ethernet
#       bridge that acts like a hub.
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNetwork import HappyNetwork
import happy.HappyNetworkAddress
import happy.HappyNetworkDelete
import happy.HappyNetworkState

options = {}
options["quiet"] = False
options["network_id"] = None
options["type"] = None


def option():
    return options.copy()


class HappyNetworkAdd(HappyNetwork):
    """
    happy-network-add creates a new ethernet bridge to represents one virtual network.

    happy-network-add [-h --help] [-q --quiet] [-i --id <NETWORK_NAME>]
                      [-t --type <TYPE>]

                      TYPE : thread, wifi, wan, cellular, out-of-band

    Example:
    $ happy-network-add Home thread
        Creates a Thread network called Home

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)

        self.quiet = opts["quiet"]
        self.network_id = opts["network_id"]
        self.type = opts["type"]

    def __deleteExistingNetwork(self):
        options = happy.HappyNetworkDelete.option()
        options["network_id"] = self.network_id
        options["quiet"] = self.quiet
        delNetwork = happy.HappyNetworkDelete.HappyNetworkDelete(options)
        delNetwork.run()

        self.readState()

    def __pre_check(self):
        # Check if the name of the new network is given
        if not self.network_id:
            emsg = "Missing name of the new virtual network that should be created."
            self.logger.error("[localhost] HappyNetworkAdd: %s" % (emsg))
            self.exit()

        # Check if dot is in the name
        if self.isDomainName(self.network_id):
            emsg = "Using . (dot) in the name is not allowed."
            self.logger.error("[localhost] HappyNetworkAdd: %s" % (emsg))
            self.exit()

        # Check if the type of the new network is given
        if not self.type:
            emsg = "Missing type of the new virtual network that should be created."
            self.logger.error("[%s] HappyNetworkAdd: %s" % (self.network_id, emsg))
            self.exit()

        # Check if the type of the new network is given
        if self.type.lower() not in self.network_type.keys():
            emsg = "Invalid virtual network type: " + self.type + "."
            self.logger.error("[%s] HappyNetworkAdd: %s" % (self.network_id, emsg))
            self.exit()

        self.type = self.type.lower()

        # Check if bridge name won't be too long
        if len(self.uniquePrefix(self.network_id)) > 15:
            emsg = "network name or state ID too long (%s, %s)." % (self.network_id, self.getStateId())
            self.logger.error("[%s] HappyNetworkAdd: %s" % (self.network_id, emsg))
            self.exit()

        # Check if the name of new network is not a duplicate (that it does not already exists).
        if self._networkExists():
            emsg = "virtual network %s already exists." % (self.network_id)
            self.logger.warning("[%s] HappyNetworkAdd: %s" % (self.network_id, emsg))
            self.__deleteExistingNetwork()

    def __create_network(self):
        # Create namespace for bridge
        cmd = "ip netns add " + self.uniquePrefix(self.network_id)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "brctl addbr " + self.uniquePrefix(self.network_id)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtNetwork(self.network_id, cmd)

    def __post_check(self):
        if not self._networkExists():
            emsg = "Failed to create virtual network."
            self.logger.error("[%s] HappyNetworkAdd: %s" % (self.network_id, emsg))
            self.exit()

    def __setup_hub(self):
        cmd = "brctl setageing " + self.uniquePrefix(self.network_id) + " 0"
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNetwork(self.network_id, cmd)

    def __add_new_network_state(self):
        new_network = {}
        new_network["interface"] = {}
        new_network["type"] = self.type
        new_network["state"] = "DOWN"
        new_network["prefix"] = {}
        new_network["gateway"] = None

        self.setNetwork(self.network_id, new_network)

    def __network_up(self):
        options = happy.HappyNetworkState.option()
        options["network_id"] = self.network_id
        options["quiet"] = self.quiet
        options["up"] = True
        upNetwork = happy.HappyNetworkState.HappyNetworkState(options)
        upNetwork.run()

        self.readState()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            # Write the state before creating the namespace; otherwise, the
            # namespace can be leaked by a SIGTERM received before
            # the state has been written
            self.__add_new_network_state()

            self.writeState()

            self.__create_network()

            self.__post_check()

            self.__setup_hub()

        self.__network_up()

        return ReturnMsg(0)
