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
#       Implements the Plaid class, to use the Faster Than Realtime
#       framework in Happy tests
#

import os
import sys
import glob
import re
import subprocess
from distutils.version import StrictVersion

from happy.State import State
from happy.Utils import *
import happy.HappyProcessStart
import happy.HappyNetworkAdd
import happy.HappyNetworkDelete
import happy.HappyNodeDelete
import happy.HappyNodeList
import happy.HappyNodeJoin
import happy.HappyStateDelete

options = {"quiet": True,
           "strace": True,
           "server_node_id": None,
           "interface": "wpan0",
           "server_ip_address": None,
           "port": 9001,
           "num_clients": 1,
           "max_time_at_high_speed_secs": None,
           "server_tag": "PLAID-SERVER",
           "network_prefix": "fd11:1111:1111:2222::"}


def default_options():
    return options.copy()

plaid_server_node_id = "plaid_server"
plaid_network_id = "plaid_network"


def deletePlaidNetwork():

    print "Deleting the plaid network"

    node_delete_options = happy.HappyNodeDelete.option()
    node_delete_options["node_id"] = plaid_server_node_id
    node_delete_options["quiet"] = False
    node_delete_cmd = happy.HappyNodeDelete.HappyNodeDelete(node_delete_options)
    node_delete_cmd.run()

    network_delete_options = happy.HappyNetworkDelete.option()
    network_delete_options["quiet"] = False
    network_delete_options["network_id"] = plaid_network_id
    network_delete_cmd = happy.HappyNetworkDelete.HappyNetworkDelete(network_delete_options)
    network_delete_cmd.run()

    state = happy.State.State()
    print "state.isStateEmpty(): " + str(state.isStateEmpty())

    if state.isStateEmpty():
        print "The happy state is now empty, deleting the file"
        state_delete_options = happy.HappyStateDelete.option()
        state_delete_options["quiet"] = True
        state_delete_cmd = happy.HappyStateDelete.HappyStateDelete(state_delete_options)
        state_delete_cmd.run()


class Plaid(State):
    def __init__(self, opts):
        State.__init__(self)

        self.min_supported_plaid_version = "1.2"

        self.__dict__.update(opts)

        self.plaid_happy_conf_path = self.__get_plaid_happy_conf_path()
        self.plaid_path = self.plaid_happy_conf_path

        self.lib_path = None
        self.server_path = None

        if self.plaid_path:
            self.lib_path = self.__lookup_plaid_file("/src/.libs/libPlaidClient.so.*.*.*")
            self.server_path = self.__lookup_plaid_file("/src/plaid-server")
            self.__check_installed_version_of_plaid()

    def __check_installed_version_of_plaid(self):
        plaid_version_output = subprocess.check_output([self.server_path, "--version"])
        version_line = plaid_version_output.split("\n")[0]
        plaid_version = re.search(r"Plaid (\S*)", version_line).group(1)

        if StrictVersion(plaid_version) < StrictVersion(self.min_supported_plaid_version):
            emsg = "This version of Happy requires Plaid version " + self.min_supported_plaid_version + "; found " + plaid_version
            self.logger.error("[localhost] Plaid: %s" % (emsg))
            sys.exit(1)

    def __get_plaid_happy_conf_path(self):
        plaid_happy_conf_path = None
        if "plaid_path" in self.configuration.keys():
            plaid_happy_conf_path = self.configuration["plaid_path"]
            emsg = "Found plaid path: %s." % (plaid_happy_conf_path)
            self.logger.debug("[localhost] Plaid: %s" % (emsg))
        return plaid_happy_conf_path

    def __lookup_plaid_file(self, file_name_glob):
        glob_path = self.plaid_path + file_name_glob
        glob_list = glob.glob(glob_path)
        if len(glob_list) == 0:
            emsg = "Plaid path %s does not exist." % (glob_path)
            self.logger.error("[localhost] Plaid: %s" % (emsg))
            sys.exit(1)

        if len(glob_list) > 1:
            emsg = "Found too many versions of plaid file %s." % (glob_path)
            self.logger.error("[localhost] Plaid: %s" % (emsg))
            sys.exit(1)

        file_path = glob_list[0]
        return file_path

    def __create_plaid_network(self):
        # Check if the parallel network already exists
        happy_network = happy.HappyNetwork.HappyNetwork(plaid_network_id)

        if not happy_network._networkExists():
            # Create a parallel network
            network_add_options = happy.HappyNetworkAdd.option()
            network_add_options["network_id"] = plaid_network_id
            network_add_options["type"] = "out-of-band"
            network_add_options["quiet"] = True
            network_add_cmd = happy.HappyNetworkAdd.HappyNetworkAdd(network_add_options)
            network_add_cmd.run()

            network_address_options = happy.HappyNetworkAddress.option()
            network_address_options["network_id"] = plaid_network_id
            network_address_options["add"] = True
            network_address_options["address"] = self.network_prefix
            network_address_options["quiet"] = True
            network_address_cmd = happy.HappyNetworkAddress.HappyNetworkAddress(network_address_options)
            network_address_cmd.run()

            # create a node for the plaid server
            node_add_options = happy.HappyNodeAdd.option()
            node_add_options["node_id"] = plaid_server_node_id
            node_add_options["quiet"] = True
            node_add_cmd = happy.HappyNodeAdd.HappyNodeAdd(node_add_options)
            node_add_cmd.run()

            # add the server to the plaid network
            node_join_options = happy.HappyNodeJoin.option()
            node_join_options["node_id"] = plaid_server_node_id
            node_join_options["quiet"] = True
            node_join_options["network_id"] = plaid_network_id
            node_join_cmd = happy.HappyNodeJoin.HappyNodeJoin(node_join_options)
            node_join_cmd.run()

            with self.getStateLockManager():
                self.readState()

    def isPlaidConfigured(self):
        # Plaid is not yet supported on lwip
        running_on_lwip = ("WEAVE_SYSTEM_CONFIG_USE_LWIP" in os.environ.keys() and
                           os.environ["WEAVE_SYSTEM_CONFIG_USE_LWIP"] == "1")
        return self.plaid_path is not None and not running_on_lwip

    def getPlaidClientLibEnv(self, client_node_id):

        addresses = self.getNodeAddressesOnNetwork(plaid_network_id, client_node_id)
        try:
            client_ip_addr = addresses[0]
        except IndexError:
            emsg = "%s joining the plaid network" % (client_node_id)
            self.logger.debug("[localhost] Plaid: %s" % (emsg))
            node_join_options = happy.HappyNodeJoin.option()
            node_join_options["node_id"] = client_node_id
            node_join_options["quiet"] = True
            node_join_options["network_id"] = plaid_network_id
            node_join_cmd = happy.HappyNodeJoin.HappyNodeJoin(node_join_options)
            node_join_cmd.run()

            with self.getStateLockManager():
                self.readState()

            # try again
            addresses = self.getNodeAddressesOnNetwork(plaid_network_id, client_node_id)
            client_ip_addr = addresses[0]

        interface = self.getNodeInterfacesOnNetwork(plaid_network_id, client_node_id)[0]

        env = {"PLAID_PROTOCOL_INTF_NAME": interface,
               "PLAID_PROTOCOL_SERVER_ADDR": self.server_ip_address,
               "PLAID_PROTOCOL_SERVER_PORT": str(self.port),
               "PLAID_PROTOCOL_CLIENT_ADDR": client_ip_addr,
               "LD_PRELOAD": self.lib_path
               }
        return env

    def startPlaidServerProcess(self):

        self.__create_plaid_network()

        addresses = self.getNodeAddressesOnNetwork(plaid_network_id, plaid_server_node_id)
        self.server_ip_address = addresses[0]

        emsg = "startPlaidServerProcess %s at %s node." % (self.server_tag, plaid_server_node_id)
        self.logger.debug("[%s] Plaid: %s" % (plaid_server_node_id, emsg))

        interface = self.getNodeInterfacesOnNetwork(plaid_network_id, plaid_server_node_id)[0]

        cmd = self.server_path
        cmd += " " + self.server_ip_address
        cmd += " " + interface
        cmd += " " + str(self.port)
        cmd += " " + str(self.num_clients)
        if self.max_time_at_high_speed_secs:
            cmd += " --maxplaidtime " + str(self.max_time_at_high_speed_secs)

        options = happy.HappyProcessStart.option()
        options["quiet"] = self.quiet
        options["node_id"] = plaid_server_node_id
        options["tag"] = self.server_tag
        options["command"] = cmd
        options["strace"] = self.strace
        options["sync_on_output"] = "Server: listening on interface"

        proc = happy.HappyProcessStart.HappyProcessStart(options)
        proc.run()

    def stopPlaidServerProcess(self):
        emsg = "stop_weave_process %s at %s node." % (self.server_tag, plaid_server_node_id)
        self.logger.debug("[%s] Plaid: %s" % (plaid_server_node_id, emsg))

        options = happy.HappyProcessStop.option()
        options["quiet"] = self.quiet
        options["node_id"] = plaid_server_node_id
        options["tag"] = self.server_tag

        stop_server = happy.HappyProcessStop.HappyProcessStop(options)
        stop_server.run()
