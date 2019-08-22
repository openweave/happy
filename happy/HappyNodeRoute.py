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
#       Implements HappyNodeRoute class that controls nodes IP routes.
#
#       This is a wrapper around Linux ip-address command.
#

import os
import re
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.utils.IP import IP
from happy.HappyNode import HappyNode
from happy.HappyNetwork import HappyNetwork
import happy.HappyNodeDelete

options = {}
options["quiet"] = False
options["node_id"] = None
options["add"] = False
options["delete"] = False
options["to"] = None
options["via"] = None
options["prefix"] = None
options["record"] = True
options["isp"] = None
options["seed"] = None
options["route_type"] = None


def option():
    return options.copy()


class HappyNodeRoute(HappyNode, HappyNetwork):
    """
    Manages virtual node IP routes.

    happy-node-route [-h --help] [-q --quiet] [-a --add] [-d --delete]
                     [-i --id <NETWORK_NAME>] [-t --to (<IP_ADDR>|default)]
                     [-v --via (<IP_ADDR>|<NODE_NAME>|<IFACE>)] [-p --prefix <IP_ADDR>]
                     [-s --isp <ISP>] [-e --seed <SEED>]

        -i --id     Required. Node to add routes to. Find using happy-node-list or
                    happy-state.
        -t --to     The destination address. Can be an IP address or 'default'. Use 'default'
                    to ensure compatability of a saved Happy topology across different Linux
                    hosts.
        -v --via    The gateway address of a target network, if the route spans multiple
                    networks. Can be an IP address, <NODE_NAME>, or <IFACE>. Use <NODE_NAME>
                    or <IFACE> to ensure compatability of a saved Happy topology across
                    different Linux hosts. When using <NODE_NAME> or <IFACE>, routes for
                    both IPv4 and IPv6 are created as needed.
        -p --prefix Gateway route prefix. Required if the gateway has more than one IP
                    address.
        -s --isp    Optional. The name of the routing table.
        -e --seed   Optional. Route priority in the routing table. Range: 0-255
        -y --type   Optional. Ip type of the node's route IP address, one of: v4, v6

    Examples:
    $ happy-node-route BorderRouter default 2001:0db8:0111:0001
        Adds a route to BorderRouter's default route via the 2001:0db8:0111:0001 address.

    $ happy-node-route ThreadNode default wpan0
        Adds a route to ThreadNode's default route via the wpan0 interface.

    $ happy-node-route -i ThreadNode -t default -v wpan0 --isp main --seed 100
        Adds a route to ThreadNode's default route via the wpan0 interface, as well as to
        the main routing table.

    $ happy-node-route -d -i ThreadNode -t default -v wpan0
        Deletes ThreadNode's default route via the wpan0 interface.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)
        HappyNetwork.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.add = opts["add"]
        self.delete = opts["delete"]
        self.to = opts["to"]
        self.via = opts["via"]
        self.prefix = opts["prefix"]
        self.record = opts["record"]
        if "weave_service_address" in os.environ.keys():
            tier = os.environ['weave_service_address'].split(".")[3][0:3]
        else:
            tier = "test"
        self.route_table = (tier + opts["isp"] + '_table') if opts["isp"] else None
        self.route_priority = opts["seed"]
        self.via_device = None
        self.via_address = None
        self.route_type = opts["route_type"]

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the new virtual node that IP routes should be managed."
            self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
            self.exit()

        # Check if the name of new node is not a duplicate (that it does not already exists).
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.warning("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))

        if not self.delete:
            self.add = True

        # Check if address is given
        if not self.to:
            emsg = "Missing address for virtual node destination (to)."
            self.logger.error("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check if address is given
        if not self.via:
            emsg = "Missing address for virtual gateway (via)."
            self.logger.error("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check for mix IP addresses
        if IP.isIpAddress(self.to) and IP.isIpAddress(self.via) and IP.isIpv6(self.to) != IP.isIpv6(self.via):
            emsg = "Mixing addresses %s and %s." % (self.to, self.via)
            self.logger.error("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))
            self.exit()

        # Check if destination is a node
        if self.to != "default" and not IP.isIpAddress(self.to):
            if not self._nodeExists(self.to):
                emsg = "Don't know what %s to-address is. If it is a node, it can't be found." % (self.to)
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()
            else:
                # 'to' is a node
                emsg = "Destination address must be 'default' or a IP address."
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

        if IP.isIpAddress(self.to):
            self.to = IP.paddingZeros(self.to)

        # Check if gateway is a node
        if IP.isIpAddress(self.via):
            self.via_address = self.via
            self.via_address = IP.paddingZeros(self.via_address)
            return

        if self._nodeInterfaceExists(self.via):
            self.via_device = self.via
            return

        if not self._nodeExists(self.via):
            emsg = "Don't know what %s via-address is. If it is a node, it can't be found." % (self.to)
            self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
            self.exit()

        this_node_networks = self.getNodeNetworkIds(self.node_id)
        gateway_networks = self.getNodeNetworkIds(self.via)
        common_networks = list(set(this_node_networks).intersection(gateway_networks))

        if len(common_networks) == 0:
            emsg = "Node %s and gateway node %s are not on the same network." % \
                (self.node_id, self.via)
            self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
            self.exit()

        if len(common_networks) > 1 and not self.prefix:
            emsg = "Node %s and gateway %s share more than one network. Need gateway prefix to disambiguate." % \
                (self.node_id, self.via)
            self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
            self.exit()

        if not self.prefix:

            gateway_addresses = self.getNodeAddressesOnNetwork(common_networks[0], self.via)

            if len(gateway_addresses) == 0:
                emsg = "Gateway node (via) %s does not have any IP addresses." % \
                    (self.via)
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

            if len(gateway_addresses) > 1 and self.prefix is None:
                emsg = "Node %s has more than one IP address. Need gateway prefix to disambiguate." % \
                    (self.via)
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

            # We find gateway address without using prefix.
            self.via_address = gateway_addresses[0]
            return

        else:
            if not IP.isIpAddress(self.prefix):
                emsg = "Prefix %s is not a valid IP address."
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

            self.ip_prefix, self.ip_mask = IP.splitAddressMask(self.prefix)
            self.prefix = IP.getPrefix(self.ip_prefix, self.ip_mask)

            gateway_addresses = self.getNodeAddressesOnNetworkOnPrefix(common_networks[0], self.prefix, self.via)

            if len(gateway_addresses) == 0:
                emsg = "Cannot find any IP address on %s with prefix %s." % (self.via, self.prefix)
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

            if len(gateway_addresses) > 1:
                emsg = "Found more than one IP address on %s with prefix %s. (%s)" % \
                  (self.via, self.prefix, ",".join(gateway_addresses))
                self.logger.error("[localhost] HappyNodeRoute: %s" % (emsg))
                self.exit()

            self.via_address = gateway_addresses[0]

    def rt_table_update(self, priority, table_id, node):
        need_overrite = False
        f = open('/etc/iproute2/rt_tables', 'rt')
        rt_content = f.read()
        if table_id not in rt_content:
            rt_content = rt_content + '\n' + '%d\t%s\n' % (priority, table_id)
            with open('/tmp/rt_tables.tmp', 'wt') as tmpf:
                tmpf.write(rt_content)
            need_overrite = True
        f.close()
        if need_overrite is True:
            cmd = 'mv /tmp/rt_tables.tmp /etc/iproute2/rt_tables'
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(node, cmd)

    def add_route_rule(self, addr, table, via_address, interface, node):
        cmd = 'ip rule add from %s lookup %s' % (addr, table)
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(node, cmd)
        cmd = 'ip route add default via %s dev %s table %s' % (via_address, interface, table)
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(node, cmd)

    def remove_route_rule(self, table, node):
        cmd = 'ip rule'
        cmd = self.runAsRoot(cmd)
        output = self.CallAtNodeForOutput(node, cmd)
        match = re.search(table, ''.join(output))
        if match:
            cmd = 'ip rule delete lookup %s' % table
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(node, cmd)
            cmd = 'ip route delete default table %s' % table
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(node, cmd)

    def __add_route(self):
        if self.to == "default" and self.via_device:
            self.__call_add_route(4)
            self.__call_add_route(6)
        else:
            if IP.isIpv6(self.to) or IP.isIpv6(self.via_address):
                self.__call_add_route(6)
            else:
                self.__call_add_route(4)

    def __call_add_route(self, family):
        if self.route_table is not None and family == 4:
            self.rt_table_update(priority=self.route_priority, table_id=self.route_table, node=self.node_id)
            addr = self.getNodeAddressesOnNetwork(network_id=self.getNodeNetworkIds(self.node_id)[1], node_id=self.node_id)
            self.add_route_rule(addr=addr[1], table=self.route_table,
                                via_address=self.via_address, interface="wlan0", node=self.node_id)
        cmd = "ip"
        cmd += " -" + str(family)
        cmd += " route add " + self.to

        if self.via_address:
            cmd += " via " + self.via_address

        if self.via_device:
            cmd += " dev " + self.via_device

        ret = self.CallAtNode(self.node_id, cmd)

    def __delete_route(self):
        if self.to == "default" and self.via_device:
            self.__call_delete_route(4)
            self.__call_delete_route(6)
        else:
            if IP.isIpv6(self.to) or IP.isIpv6(self.via_address):
                self.__call_delete_route(6)
            else:
                self.__call_delete_route(4)

    def __call_delete_route(self, family):
        if self.route_table is not None and family == 4:
            self.remove_route_rule(table=self.route_table, node=self.node_id)

        cmd = "ip"
        cmd += " -" + str(family)
        cmd += " route delete " + self.to

        if self.via_address:
            cmd += " via " + self.via_address

        if self.via_device:
            cmd += " dev " + self.via_device

        ret = self.CallAtNode(self.node_id, cmd)

    def nodeIpv4TableExist(self, node_id):
        # IPv4 table
        cmd = "ip route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(node_id, cmd)
        if out is not None:
            for line in out.split("\n"):
                if "proto kernel" in line:
                    num_dot = line.split()[-1].count('.')
                    if num_dot == 3:
                        return True
        return False

    def nodeIpv4DefaultExist(self, node_id):
        # IPv4 Default
        cmd = "ip route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(node_id, cmd)
        if out is not None:
            for line in out.split("\n"):
                if "default" in line:
                    return True
        return False

    def __nodeRouteExistsViaAddress(self, to, via):
        via = IP.paddingZeros(via)
        if to != 'default':
            to = IP.paddingZeros(to)

        # IPv4
        cmd = "ip route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(self.node_id, cmd)

        if out is not None:
            for line in out.split("\n"):
                l = line.split()
                if len(l) < 3:
                    continue

                if to == 'default':
                    if l[0] == to and l[1] == "via" and IP.paddingZeros(l[2]) == via:
                        if self.route_table is not None:
                            if self.nodeIpv4TableExist(self.node_id) is True:
                                return True
                        else:
                            return True

                else:
                    if IP.paddingZeros(l[0]) == to and l[1] == "via" and IP.paddingZeros(l[2]) == via:
                        if self.route_table is not None:
                            if self.nodeIpv4TableExist(self.node_id) is True:
                                return True
                        return True

        # IPv6
        cmd = "ip -6 route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(self.node_id, cmd)

        if out is not None:
            for line in out.split("\n"):
                l = line.split()
                if len(l) < 3:
                    continue

                if IP.paddingZeros(l[0]) == to and l[1] == "via" and IP.paddingZeros(l[2]) == via:
                    return True

        return False

    def __nodeRouteExistsViaDevice(self, to, dev):
        if to != 'default':
            to = IP.paddingZeros(to)

        # IPv4
        cmd = "ip route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(self.node_id, cmd)

        if out is not None:
            for line in out.split("\n"):
                l = line.split()
                if len(l) < 3:
                    continue

                if to == 'default':
                    if l[0] == to and l[1] == "dev" and l[2] == dev:
                        if self.route_table is not None:
                            if self.nodeIpv4TableExist(self.node_id) is True:
                                return True
                        return True

                else:
                    if IP.paddingZeros(l[0]) == to and l[1] == "dev" and l[2] == dev:
                        if self.route_table is not None:
                            if self.nodeIpv4TableExist(self.node_id) is True:
                                return True
                        return True

        # IPv6
        cmd = "ip -6 route"
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtNodeForOutput(self.node_id, cmd)

        if out is not None:
            for line in out.split("\n"):
                l = line.split()
                if len(l) < 3:
                    continue

                if IP.paddingZeros(l[0]) == to and l[1] == "dev" and l[2] == dev:
                    return True

        return False

    def __nodeRouteExists(self):
        if self.via_address:
            return self.__nodeRouteExistsViaAddress(self.to, self.via_address)

        if self.via_device:
            return self.__nodeRouteExistsViaDevice(self.to, self.via_device)

    def __post_check(self):
        if self.__nodeRouteExists():
            if self.add:
                return

            emsg = "Failed to remove route to %s via %s at virtual node %s." % \
                (self.to, self.via, self.node_id)

            self.logger.error("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))
            self.exit()

        else:
            if self.delete:
                return

            emsg = "Failed to add route to %s via %s at virtual node %s." % \
                (self.to, self.via, self.node_id)

            self.logger.error("[%s] HappyNodeRoute: %s" % (self.node_id, emsg))
            self.exit()

    def __update_state(self):
        if not self.record:
            return

        if self.add:
            new_route = {}
            new_route["to"] = self.to
            new_route["via"] = self.via
            new_route["prefix"] = self.prefix

            self.setNodeRoute(self.node_id, self.to, new_route)
        else:
            self.removeNodeRoute(self.node_id, self.to)

    def run(self):
        # query node's route ip in v4 or v6 format.
        if not self.add and not self.delete:
            node_route_prefix = self.getNodeRoutePrefix(self.route_type, self.node_id)
            node_route_via_id = self.getNodeRouteVia(self.route_type, self.node_id)
            node_route_addrs = self.getNodeAddressesOnPrefix(node_route_prefix, node_route_via_id)

            emsg = "virtual node: {}, route_type: {}, route ip: {}".format(
                self.node_id, self.route_type, node_route_addrs)
            print emsg
        else:
            self.__pre_check()
            # only configure route for nonTAP device
            # for TAP device, route will be configured in lwip stack in weave.
            if not self.IsTapDevice(self.node_id):
                if self.route_table is not None:
                    with self.getStateLockManager(lock_id="rt"):
                        if self.add:
                            self.__add_route()
                        else:
                            self.__delete_route()
                else:
                    if self.add:
                        self.__add_route()
                    else:
                        self.__delete_route()
                self.__post_check()
            with self.getStateLockManager():
                self.__update_state()
                self.writeState()
        return ReturnMsg(0)
