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
#       Implements HappyNetworkStatus class that shows virtual networks.
#

from __future__ import absolute_import
from __future__ import print_function
import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNetwork import HappyNetwork
from six.moves import range

options = {}
options["quiet"] = False
options["network_id"] = None


def option():
    return options.copy()


class HappyNetworkStatus(HappyNetwork):
    """
    Displays virtual network information.

    happy-network-status [-h --help] [-q --quiet] [-i --id <NETWORK_NAME>]

        -i --id     Network to display information for. Find using
                    happy-network-list or happy-state.

    Examples:
    $ happy-network-status
        Displays information for all networks.

    $ happy-network-status HomeThread
        Displays information for the HomeThread network in JSON format.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNetwork.__init__(self)

        self.quiet = opts["quiet"]
        self.network_id = opts["network_id"]

    def __pre_check(self):
        # Check if the virtual network exists
        if self.network_id is not None and not self._networkExists():
            emsg = "virtual network %s does not exist" % (self.network_id)
            self.logger.error("[%s] HappyNetworkStatus: %s" % (self.network_id, emsg))
            self.exit()

    def __post_check(self):
        pass

    def __print_all_networks(self):
        print("{0: >15} {1: >12} {2: >7} {3: >44}".format("NETWORKS   Name", "Type", "State", "Prefixes"))

        for network_id in self.getNetworkIds():
            print("{0: >15} {1: >12} {2: >7}".format(network_id,
                                                     self.getNetworkType(network_id),
                                                     self.getNetworkState(network_id)), end=' ')

            prefixes = self.getNetworkPrefixes(network_id)

            if len(prefixes) == 0:
                print()
                continue

            for i in range(len(prefixes)):
                if i > 0:
                    print(" " * 36, end=' ')

                print(" {0: >40}/{1: <3}".format(prefixes[i], self.getNetworkPrefixMask(prefixes[i], network_id)))

            print()

    def run(self):
        self.__pre_check()

        if self.network_id is None:
            self.__print_all_networks()
            return 0

        data_state = json.dumps(self.getNetwork(self.network_id), sort_keys=True, indent=4)
        emsg = "virtual network state: " + self.network_id

        print(emsg)

        self.logger.info("[%s] HappyNetworkStatus: %s" % (self.network_id, emsg))

        print(data_state)

        for line in data_state.split("\n"):
            if line is None or len(line) == 0:
                continue

            self.logger.info("[%s] HappyNetworkStatus: %s" % (self.network_id, line))

        self.__post_check()

        return ReturnMsg(0)
