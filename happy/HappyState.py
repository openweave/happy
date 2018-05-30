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
#       Implements HappyState class that reports virtual network topology setup information.
#

import itertools
import json
import os
import sys

from happy.Utils import *
from happy.State import State
import happy.HappyNodeStatus
import happy.HappyNetworkStatus


try:
    import networkx as nx
    has_networkx = True
except Exception:
    has_networkx = False

try:
    import matplotlib.pyplot as plt
    has_matplotlib = True
except Exception:
    has_matplotlib = False

options = {}
options["quiet"] = False
options["save"] = None
options["graph"] = None
options["log"] = False
options["json"] = False
options["unlock"] = False
options["id"] = False
options["all"] = False


def option():
    return options.copy()


class HappyState(State):
    """
    Displays the state of the Happy network topology.

    happy-state [-h --help] [-q --quiet] [-s --save <JSON_FILE>] [-g --graph]
                [-l --logs] [-j --json] [-u --unlock] [-i --id] [-a --all]

        -s --save   Saves the current network topology state in a JSON file.
        -g --graph  Generates a network topology graph.
        -l --logs   Display Happy run-time logs. Run in a separate terminal
                    window to observe logs while using Happy.
        -j --json   Display the current state in JSON format.
        -u --unlock Force unlock the Happy state file (~/.happy_state.json).
        -i --id     Displays all known state IDs.
        -a --all    Displays the network topology state for all known states.

    Examples:
    $ happy-state
        Displays the current network topology state.

    $ happy-state -s mystate.json
        Saves the current network topology state in mystate.json.

    $ happy-state -a -l
        Displays Happy run-time logs for all known states.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        State.__init__(self)

        self.quiet = opts["quiet"]
        self.save = opts["save"]
        self.graph = opts["graph"]
        self.log = opts["log"]
        self.json = opts["json"]
        self.unlock_state = opts["unlock"]
        self.show_id = opts["id"]
        self.all = opts["all"]

    def __pre_check(self):
        pass

    def __print_data_state(self):
        if self.quiet or self.graph or self.save or self.log or self.json or \
           self.unlock_state or self.show_id:
            return

        self.__print_own_state()

        if self.all:
            states = self.__get_state_ids()
            this_state = self.getStateId()

            og_state = os.environ.get(self.state_environ, None)

            for state in states:
                if state == this_state:
                    continue
                os.environ[self.state_environ] = state
                cmd = HappyState(option())
                cmd.run()

            if og_state is None:
                os.environ.pop(self.state_environ)
            else:
                os.environ[self.state_environ] = og_state

    def __print_own_state(self):

        print

        print "State Name: ",
        print self.getStateId()

        print

        options = happy.HappyNetworkStatus.option()
        options["quiet"] = self.quiet
        nets = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        nets.run()

        print

        options = happy.HappyNodeStatus.option()
        options["quiet"] = self.quiet
        nodes = happy.HappyNodeStatus.HappyNodeStatus(options)
        nodes.run()

        print

    def __print_json_state(self):
        if self.json:
            json_data = json.dumps(self.state, sort_keys=True, indent=4)
            print
            print json_data
            print

    def __save_state(self):
        if self.save is None:
            return

        if self.save.split(".")[-1] != "json":
            self.save = self.save + ".json"

        try:
            json_data = json.dumps(self.state, sort_keys=True, indent=4)
        except Exception:
            print "Failed to save state file: %s" % (self.save)
            self.logger.error("calls self.exit()")
            self.exit()

        with open(self.save, 'w') as jfile:
            jfile.write(json_data)

    def __graph_state(self):
        if self.graph is None:
            return

        if not has_networkx:
            emsg = "Cannot generate graph. Localhost is missing networkx libraries."
            self.logger.warning("[localhost] HappyState: %s" % (emsg))
            print hyellow(emsg)
            extra_msg = "Try,   apt-get install python-networkx"
            print hyellow(extra_msg)
            return

        if not has_matplotlib:
            emsg = "Cannot generate graph. Localhost is missing matplotlib libraries."
            self.logger.warning("[localhost] HappyState: %s" % (emsg))
            print hyellow(emsg)
            extra_msg = "Try,   apt-get install python-matplotlib"
            print hyellow(extra_msg)
            return

        G = nx.Graph()

        node_points = []
        node_colors = []
        node_sizes = []
        node_labels = {}

        for node_id in self.getNodeIds():
            node_points.append(node_id)
            node_colors.append("#1FBCE0")
            node_sizes.append(3000)
            node_labels[node_id] = node_id

        edge_points = []
        edge_weights = []
        edge_colors = []

        for network_id in self.getNetworkIds():
            color = None
            weight = None
            network_type = self.getNetworkType(network_id)

            if network_type == "thread":
                color = "green"
                weight = 1

            if network_type == "wifi":
                color = "blue"
                weight = 1.5

            if network_type == "wan":
                color = "red"
                weigth = 2

            if network_type == "cellular":
                color = "black"
                weigth = 2

            if network_type == "out-of-band":
                color = "yellow"
                weigth = 2

            if color is None or weight is None:
                continue

            nodes = []

            for interface_id in self.getNetworkLinkIds(network_id):
                nodes.append(self.getLinkNode(interface_id))

            # cartesian product assuming everybody is connected

            points = list(itertools.product(nodes, nodes))
            edge_points += points
            edge_colors += [color] * len(points)
            edge_weights += [weight] * len(points)

        G.add_nodes_from(node_points)
        G.add_edges_from(edge_points)

        pos = nx.shell_layout(G)
        pos = nx.spring_layout(G)

        nx.draw_networkx_nodes(G, pos, nodelist=node_points, node_color=node_colors, node_size=node_sizes)
        nx.draw_networkx_edges(G, pos, edgelist=edge_points, width=edge_weights, edge_color=edge_colors)
        nx.draw_networkx_labels(G, pos, node_labels, font_size=14)

        plt.axis('off')

        if self.save:
            if self.save.split(".")[-1] != "png":
                self.save = self.save + ".png"

        else:
            plt.show()

    def __post_check(self):
        pass

    def __try_unlock(self):
        if self.unlock_state:
            lock_manager = self.getStateLockManager()
            lock_manager.break_lock()

    def __get_state_ids(self):
        states = []
        files = os.listdir(os.path.dirname(os.path.expanduser(self.state_file_prefix)))

        for f in files:
            if f.endswith(self.state_file_suffix):
                s = f.rstrip(self.state_file_suffix)
                s = s.lstrip(".")
                states.append(s)

        return states

    def __show_state_id(self):
        if self.show_id:
            states = self.__get_state_ids()
            this_state = self.getStateId()
            print this_state + " <"

            for s in states:
                if s == this_state:
                    continue
                print s

    def __get_log_path(self):
        file_path = None

        if "handlers" in self.log_conf.keys():
            if "file" in self.log_conf["handlers"].keys():
                if "filename" in self.log_conf["handlers"]["file"].keys():
                    file_path = self.log_conf["handlers"]["file"]["filename"]

        return file_path

    def __show_logs(self):
        if not self.log:
            return

        if self.all:
            states = self.__get_state_ids()
            og_state = os.environ.get(self.state_environ, None)

            logs = ['tail']

            for state in states:
                os.environ[self.state_environ] = state
                hs = HappyState(option())
                log_file = hs.__get_log_path()
                if log_file:
                    logs.append(log_file)

            if og_state is None:
                os.environ.pop(self.state_environ)
            else:
                os.environ[self.state_environ] = og_state

            cmd = ' -f '.join(logs)

        else:
            file_path = self.__get_log_path()

            if file_path is None:
                emsg = "Happy aggregated logs file is unknown."
                self.logger.warning("[localhost] HappyState: %s" % (emsg))
                print hyellow(emsg)
                return

            cmd = "tail -n 100 -f  " + file_path

        print hgreen("Happy Runtime Logs. Press <Ctrl-C> to exit.")
        os.system(cmd)

    def run(self):
        self.__pre_check()

        self.__print_data_state()
        self.__print_json_state()
        self.__try_unlock()

        self.__show_state_id()
        self.__save_state()
        self.__graph_state()
        self.__show_logs()

        self.__post_check()
