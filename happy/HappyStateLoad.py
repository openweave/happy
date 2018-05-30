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
#       Implements HappyStateLoad class that sets up virtual fabric topology.
#
#       A virtual fabric topology consists of virtual nodes and networks.
#

import json
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.State import State
import happy.HappyNodeAdd
import happy.HappyNodeJoin
import happy.HappyNodeRoute
import happy.HappyNodeTmux
import happy.HappyNetworkAdd
import happy.HappyNetworkAddress
import happy.HappyNetworkRoute

options = {}
options["quiet"] = False
options["json_file"] = None


def option():
    return options.copy()


class HappyStateLoad(State):
    """
    Loads a virtual network topology from a JSON file.

    happy-state-load [-h --help] [-q --quiet] [-f --file <JSON_FILE>]

        -f --file   Required. A valid JSON file with the topology to load.

    Example:
    $ happy-state-load mystate.json
        Creates a virtual network topology based on the state described
        in mystate.json.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        State.__init__(self)

        self.quiet = opts["quiet"]
        self.new_json_file = opts["json_file"]

    def __pre_check(self):
        # Check if the name of the new node is given
        if self.new_json_file is None:
            emsg = "Missing name of file that specifies virtual network topology."
            self.logger.error("[localhost] HappyStateLoad: %s" % (emsg))
            self.exit()

        # Check if json file exists
            if not os.path.exists(self.new_json_file):
                emsg = "Cannot find the configuration file %s" % (self.new_json_file)
                self.logger.error("[localhost] HappyStateLoad: %s" % emsg)
                self.exit()

        self.new_json_file = os.path.realpath(self.new_json_file)

        emsg = "Loading Happy state from file %s." % (self.new_json_file)
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

    def __load_JSON(self):
        emsg = "Import state file %s." % (self.new_json_file)
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        try:
            with open(self.new_json_file, 'r') as jfile:
                json_data = jfile.read()

            self.network_topology = json.loads(json_data)

        except Exception:
            emsg = "Failed to load JSON state file: %s" % (self.new_json_file)
            self.logger.error("[localhost] HappyStateLoad: %s" % emsg)
            self.exit()

    def __create_nodes(self):
        emsg = "Create nodes."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for node_id in self.getNodeIds(self.network_topology):
            node = self.getNode(node_id, self.network_topology)
            node_type = self.getNodeType(node_id, self.network_topology)

            options = happy.HappyNodeAdd.option()
            options["quiet"] = self.quiet
            options["node_id"] = node_id
            options["type"] = node_type

            obj = happy.HappyNodeAdd.HappyNodeAdd(options)
            ret = obj.run()

            self.readState()

    def __create_networks(self):
        emsg = "Create networks."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for network_id in self.getNetworkIds(self.network_topology):
            network = self.getNetwork(network_id, self.network_topology)

            options = happy.HappyNetworkAdd.option()
            options["quiet"] = self.quiet
            options["network_id"] = network_id
            options["type"] = network["type"]

            obj = happy.HappyNetworkAdd.HappyNetworkAdd(options)
            ret = obj.run()

            self.readState()

    def __nodes_join_networks(self):
        emsg = "Nodes join networks."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for link_id in self.getLinkIds(self.network_topology):
            link = self.getLink(link_id, self.network_topology)

            options = happy.HappyNodeJoin.option()
            options["quiet"] = self.quiet
            options["node_id"] = link["node"]
            options["network_id"] = link["network"]
            options["tap"] = link["tap"]

            if "fix_hw_addr" in link.keys():
                options["fix_hw_addr"] = link["fix_hw_addr"]
            else:
                options["fix_hw_addr"] = None

            obj = happy.HappyNodeJoin.HappyNodeJoin(options)
            ret = obj.run()

            self.readState()

    def __add_network_prefixes(self):
        emsg = "Adding network prefixes."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for network_id in self.getNetworkIds(self.network_topology):
            network = self.getNetwork(network_id, self.network_topology)

            prefixes = self.getNetworkPrefixes(network_id, self.network_topology)

            for prefix in prefixes:
                mask = self.getNetworkPrefixMask(prefix, network_id, self.network_topology)

                options = happy.HappyNetworkAddress.option()
                options["network_id"] = network_id
                options["quiet"] = self.quiet
                options["add"] = True
                options["address"] = str(prefix) + "/" + str(mask)

                prf = happy.HappyNetworkAddress.HappyNetworkAddress(options)
                ret = prf.run()

                self.readState()

    def __add_network_routes(self):
        emsg = "Adding network routes."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for network_id in self.getNetworkIds(self.network_topology):
            routes = self.getNetworkRoutes(network_id, self.network_topology)
            for route_to in routes.keys():
                route_record = self.getNetworkRoute(route_to, network_id, self.network_topology)

                options = happy.HappyNetworkRoute.option()
                options["quiet"] = self.quiet
                options["add"] = True
                options["network_id"] = network_id
                options["prefix"] = route_record["prefix"]
                options["to"] = route_record["to"]
                options["via"] = route_record["via"]

                hnr = happy.HappyNetworkRoute.HappyNetworkRoute(options)
                ret = hnr.run()

                self.readState()

    def __add_node_routes(self):
        emsg = "Adding nodes' routes."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for node_id in self.getNodeIds(self.network_topology):
            routes = self.getNodeRoutes(node_id, self.network_topology)
            for route_to in routes.keys():
                route_record = self.getNodeRoute(route_to, node_id, self.network_topology)
                existing_route_record = self.getNodeRoute(route_to, node_id, self.state)

                if existing_route_record != {} and route_record["via"] == existing_route_record["via"]:
                    # Node already have the route record, skip it
                    emsg = "Route record to %s via %s already exists." % (route_to, existing_route_record["via"])
                    self.logger.info("[%s] HappyStateLoad: %s" % (node_id, emsg))
                    continue

                options = happy.HappyNodeRoute.option()
                options["quiet"] = self.quiet
                options["add"] = True
                options["node_id"] = node_id
                options["to"] = route_record["to"]
                options["via"] = route_record["via"]
                options["prefix"] = route_record["prefix"]

                noder = happy.HappyNodeRoute.HappyNodeRoute(options)
                ret = noder.run()

                self.readState()

    def __start_nodes_tmux(self):
        emsg = "Start tmux sessions."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

        for node_id in self.getNodeIds(self.network_topology):
            tmux_ids = self.getNodeTmuxSessionIds(node_id, self.network_topology)
            for tmux_id in tmux_ids:

                options = happy.HappyNodeTmux.option()
                options["node_id"] = node_id
                options["quiet"] = self.quiet
                options["attach"] = False
                options["run_as_user"] = self.getNodeTmuxSessionUser(tmux_id,
                                                                     node_id,
                                                                     self.network_topology)

                ntmux = happy.HappyNodeTmux.HappyNodeTmux(options)
                ret = ntmux.run()

                self.readState()

    def __post_check(self):
        emsg = "Loading Happy state completed."
        self.logger.debug("[localhost] HappyStateLoad: %s" % (emsg))

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.__load_JSON()

            self.__create_nodes()

            self.__create_networks()

            self.__add_network_prefixes()

            self.__nodes_join_networks()

            self.__add_network_routes()

            self.__add_node_routes()

            self.__start_nodes_tmux()

            self.__post_check()

        return ReturnMsg(0)
