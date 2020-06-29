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
#       Implements HappyStateUnload class that removed nodes and networks from virtual topology.
#

from __future__ import absolute_import
import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.State import State
import happy.HappyNodeDelete
import happy.HappyNetworkDelete
import happy.HappyLinkDelete

options = {}
options["quiet"] = False
options["json_file"] = None


def option():
    return options.copy()


class HappyStateUnload(State):
    """
    Deletes a virtual network topology based on the state described in a
    JSON file. If the current Happy state does not match the specified JSON
    file, a partial deletion of the topology might occur.

    happy-state-unload [-h --help] [-q --quiet] [-f --file <JSON_FILE>]

        -f --file   Required. A valid JSON file with the topology to delete.

    Example:
    $ happy-state-unload mystate.json
        Deletes the network topology based on the state described in mystate.json.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        State.__init__(self)

        self.quiet = opts["quiet"]
        self.old_json_file = opts["json_file"]

    def __pre_check(self):
        # Check if the name of the new node is given
        if self.old_json_file is None:
            emsg = "Missing name of file that specifies virtual network topology."
            self.logger.error("[localhost] HappyStateUnload: %s" % (emsg))
            self.exit()

        # Check if json file exists
            if not os.path.exists(self.old_json_file):
                emsg = "Cannot find the configuration file %s" % (self.old_json_file)
                self.logger.error("[localhost] HappyStateUnload: %s" % emsg)
                self.exit()

        self.old_json_file = os.path.realpath(self.old_json_file)

        emsg = "Unloading Happy state from file %s." % (self.old_json_file)
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

    def __load_JSON(self):
        emsg = "Import state file %s." % (self.old_json_file)
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

        try:
            with open(self.old_json_file, 'r') as jfile:
                json_data = jfile.read()

            self.network_topology = json.loads(json_data)

        except Exception:
            emsg = "Failed to load JSON state file: %s" % (self.old_json_file)
            self.logger.error("[localhost] HappyStateUnload: %s" % emsg)
            self.exit()

    def __delete_nodes(self):
        emsg = "Deleting nodes."
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

        for node_id in self.getNodeIds(self.network_topology):

            options = happy.HappyNodeDelete.option()
            options["quiet"] = self.quiet
            options["node_id"] = node_id

            node = happy.HappyNodeDelete.HappyNodeDelete(options)
            ret = node.run()

            self.readState()

    def __delete_networks(self):
        emsg = "Deleting networks."
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

        for network_id in self.getNetworkIds(self.network_topology):

            options = happy.HappyNetworkDelete.option()
            options["quiet"] = self.quiet
            options["network_id"] = network_id

            network = happy.HappyNetworkDelete.HappyNetworkDelete(options)
            ret = network.run()

            self.readState()

    def __delete_links(self):
        emsg = "Deleting links."
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

        for link_id in self.getLinkIds(self.network_topology):

            options = happy.HappyLinkDelete.option()
            options["quiet"] = self.quiet
            options["link_id"] = link_id

            link = happy.HappyLinkDelete.HappyLinkDelete(options)
            ret = link.run()

            self.readState()

    def __delete_state_file(self):
        emsg = "delete state file."
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))
        if os.path.isfile(self.state_file):
            os.remove(self.state_file)

    def __post_check(self):
        emsg = "Unloading Happy state completed."
        self.logger.debug("[localhost] HappyStateUnload: %s" % (emsg))

    def run(self):

        with self.getStateLockManager():
            self.__pre_check()

            self.__load_JSON()

            self.__delete_links()

            self.__delete_networks()

            self.__delete_nodes()

            self.__post_check()

            self.writeState()

        if self.isStateEmpty():
            self.__delete_state_file()

        return ReturnMsg(0)
