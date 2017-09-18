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
#       Implements HappyHost class that interacts with host OS.
#

import os
import sys

from happy.State import State
from happy.Utils import *


class HappyHost(State):
    def __init__(self, node_id=None):
        State.__init__(self)
        self.network_type = {
            "thread": "thread",
            "wifi": "wifi",
            "wan": "wan",
            "cellular": "cellular",
            "internet": "internet",
            "tun": "tun",
            "out-of-band": "out-of-band"
        }
        self.node_link_suffix = "node"
        self.network_link_suffix = "net"
        self.ethernet_bridge_suffix = "bridge"
        self.ethernet_bridge_link = "tap"

    def _namespaceExists(self, name):
        result = os.path.isfile("/var/run/netns/%s" % (self.uniquePrefix(name)))
        msg = "Happy: namespace " + self.uniquePrefix(name)
        if result:
            msg = msg + " exists"
        else:
            msg = msg + " does not exist"
        self.logger.debug(msg)
        return result

    def getHostNamespaces(self):
        ret = []
        cmd = "ip netns list"
        nodes, _ = self.CallAtHostForOutput(cmd)

        if nodes is None:
            return ret

        nodes = nodes.split("\n")

        for record in nodes:
            if len(record) < 1:
                continue

            ret.append(record)

        return ret

    def getHostBridges(self):
        ret = []
        cmd = "brctl show"
        bridges, _ = self.CallAtHostForOutput(cmd)
        bridges = bridges.split("\n")

        for record in bridges:
            r = record.split()
            if len(r) < 1:
                continue

            if r[0] == "bridge":
                continue

            ret.append(r[0])

        return ret

    def getHostNMInterfaceStatus(self, interface_id):
        cmd = "nmcli dev status"
        cmd = self.runAsRoot(cmd)
        out, er = self.CallAtHostForOutput(cmd)
        lines = out.split("\n")

        for line in lines:
            l = line.split()
            if len(l) < 3:
                continue
            if l[0] == interface_id:
                return l[2]
        return None

    def __parse_interfaces(self, links):
        ret = []
        links = links.split("\n")

        for record in links:
            r = record.split()
            if len(r) < 2:
                continue

            if len(r[1]) < 3:
                continue

            if r[1][-1] == ":":
                r[1] = r[1][:-1]

            if '@' in r[1]:
                r[1] = r[1].split('@')[0]

            ret.append(r[1])

        return ret

    def getHostInterfaces(self):
        cmd = "ip link show"
        links, _ = self.CallAtHostForOutput(cmd)
        return self.__parse_interfaces(links)

    def getActiveNetworkLinks(self, network_id=None):
        if network_id is None:
            network_id = self.network_id

        cmd = "ip link show"
        links, _ = self.CallAtNetworkForOutput(network_id, cmd)
        return self.__parse_interfaces(links)

    def getActiveNodeLinks(self, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "ip link show"
        links, _ = self.CallAtNodeForOutput(node_id, cmd)
        return self.__parse_interfaces(links)

    def getHostTmuxSessionIds(self):
        ret = []
        cmd = "ps -x"
        output, _ = self.CallAtHostForOutput(cmd)

        if output is None:
            return []

        output = output.split("\n")

        for record in output:
            line = record.split()
            if len(line) < 11:
                continue

            if line[4] != "tmux":
                continue

            if line[5] == "-L" and line[7] == "new" and line[8] == "-s":
                tsid = line[9].strip()
                if tsid not in ret:
                    ret.append(tsid)

        return ret

    def getDefaultInterfaceName(self):
        cmd = "ip route"
        output, _ = self.CallAtHostForOutput(cmd)

        if output is None:
            return None

        output = output.split("\n")

        for record in output:
            line = record.split()
            if len(line) < 5:
                continue

            if line[0] == "default":
                return line[4]

        return None

    def waitForDAD(self):
        retval = False
        poll_interval_sec = 0.01
        max_poll_time_sec = 60
        time_slept = 0
        while True:
            cmd = "ip addr show tentative"
            out, err = self.CallAtNodeForOutput(self.node_id, cmd)
            if "tentative" not in out:
                break
            time.sleep(poll_interval_sec)
            time_slept += poll_interval_sec
            self.logger.debug("[%s] HappyHost.waitForDAD: slept %f secs" % (self.node_id, time_slept))
            poll_interval_sec *= 2
            if (time_slept > max_poll_time_sec):
                self.logger.debug("[%s] HappyNode.waitForDAD: timeout" % (self.node_id))
                self.exit()
