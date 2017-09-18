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
#       Implements HappyStateDelete class that deletes virtual network topology and its state.
#

import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *

import happy.HappyNodeDelete
import happy.HappyNetworkDelete
import happy.HappyLinkDelete
import happy.HappyNode
from happy.HappyHost import HappyHost

options = {}
options["quiet"] = False
options["force"] = False
options["all"] = False


def option():
    return options.copy()


class HappyStateDelete(HappyHost):
    """
    happy-state-delete [-h --help] [-q --quiet] [-f --force] [-a --all]

    Example:
    $ happy-state-delete --all --force
        Deletes Happy state and other host network resources without asking for confirmation.
        Very dangerous, be careful!

    $ happy-state-delete
        Only deletes nodes, links and networks that are found in the state file.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyHost.__init__(self)

        self.quiet = opts["quiet"]
        self.force = opts["force"]
        self.all = opts["all"]

    def __pre_check(self):
        lock_manager = self.getStateLockManager()
        lock_manager.break_lock()

    def __post_check(self):
        emsg = "Delete Happy state completed."
        self.logger.debug("[localhost] HappyStateDelete: %s" % (emsg))

    def __delete_state(self):
        for node_id in self.getNodeIds():
            options = happy.HappyNodeDelete.option()
            options["quiet"] = self.quiet
            options["node_id"] = node_id
            cmd = happy.HappyNodeDelete.HappyNodeDelete(options)
            ret = cmd.run()

        self.readState()

        for network_id in self.getNetworkIds():
            options = happy.HappyNetworkDelete.option()
            options["quiet"] = self.quiet
            options["network_id"] = network_id
            cmd = happy.HappyNetworkDelete.HappyNetworkDelete(options)
            ret = cmd.run()

        self.readState()

        for link_id in self.getLinkIds():
            options = happy.HappyLinkDelete.option()
            options["quiet"] = self.quiet
            options["link_id"] = link_id
            cmd = happy.HappyLinkDelete.HappyLinkDelete(options)
            ret = cmd.run()

        self.readState()

    def __delete_state_file(self):
        if os.path.isfile(self.state_file):
            os.remove(self.state_file)

    def __delete_host_netns(self):
        for node_id in self.getHostNamespaces():
            delete_it = False

            if self.force is True:
                delete_it = True
            else:
                reply = str(raw_input("Delete host namespace " + node_id + " (y/N): ")).lower().strip()
                if reply[0] == 'y':
                    delete_it = True

            if delete_it:
                options = happy.HappyNodeDelete.option()
                options["quiet"] = self.quiet
                options["node_id"] = node_id
                cmd = happy.HappyNodeDelete.HappyNodeDelete(options)
                ret = cmd.run()
            else:
                emsg = "Leaving host namespace %s as it is." % (node_id)
                self.logger.error("[localhost] HappyStateDelete: %s" % (emsg))

        self.readState()

    def __delete_host_bridges(self):
        for network_id in self.getHostBridges():
            delete_it = False

            if self.force is True:
                delete_it = True
            else:
                reply = str(raw_input("Delete host bridge " + network_id + " (y/N): ")).lower().strip()
                if reply[0] == 'y':
                    delete_it = True

            if delete_it:
                options = happy.HappyNetworkDelete.option()
                options["quiet"] = self.quiet
                options["network_id"] = network_id
                cmd = happy.HappyNetworkDelete.HappyNetworkDelete(options)
                ret = cmd.run()
            else:
                emsg = "Leaving host bridge %s as it is." % (network_id)
                self.logger.error("[localhost] HappyStateDelete: %s" % (emsg))

        self.readState()

    def __delete_host_links(self):
        for link_id in self.getHostInterfaces():
            delete_it = False

            if self.force is True:
                delete_it = True
            else:
                reply = str(raw_input("Delete host link " + link_id + " (y/N): ")).lower().strip()
                if len(reply) > 0 and reply[0] == 'y':
                    delete_it = True

            if delete_it:
                options = happy.HappyLinkDelete.option()
                options["quiet"] = self.quiet
                options["link_id"] = link_id
                cmd = happy.HappyLinkDelete.HappyLinkDelete(options)
                ret = cmd.run()
            else:
                emsg = "Leaving host link %s as it is." % (link_id)
                self.logger.error("[localhost] HappyStateDelete: %s" % (emsg))

        self.readState()

    def __cleanup_host(self):
        self.__delete_host_netns()
        self.__delete_host_bridges()
        self.__delete_host_links()

    def run(self):
        self.__pre_check()

        self.__delete_state()

        self.__delete_state_file()

        if self.all:
            self.__cleanup_host()

        self.__post_check()

        return ReturnMsg(0)
