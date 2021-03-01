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
#       Implements State class that implements methods to retrieve
#       parts of state setup.
#

from __future__ import absolute_import
import logging

from happy.utils.IP import IP
from happy.Driver import Driver
import six


class State(Driver):
    def __init__(self):
        Driver.__init__(self)

        if not bool(self.isp_state):
            self.isp_state = {}

        if not bool(self.state):
            self.state = {}

    def isStateEmpty(self, state=None):
        state = self.getState(state)

        if self.getNodeIds():
            return False

        if self.getNetworkIds():
            return False

        if self.getLinkIds():
            return False

        return True

    def getState(self, state=None):
        if state is None:
            state = self.state
        return state

    def getIspState(self, state=None):
        if state is None:
            state = self.isp_state
        return state

    def getNetNS(self, state=None):
        state = self.getState(state)
        if "netns" not in list(state.keys()):
            state["netns"] = {}
        return state["netns"]

    def getNetNSIds(self, state=None):
        netns = self.getNetNS(state)
        ids = list(netns.keys())
        ids.sort()
        return ids

    def getIdentifiers(self, state=None):
        state = self.getState(state)
        if "identifiers" not in list(state.keys()):
            state["identifiers"] = {}
        return state["identifiers"]

    def getIdentifierByNodeId(self, node_id, state=None):
        state = self.getState(state)
        if "netns" not in list(state.keys()):
            return None
        if node_id not in state["netns"]:
            return None
        return state["netns"][node_id]

    def getNodes(self, state=None):
        state = self.getState(state)
        if "node" not in list(state.keys()):
            state["node"] = {}
        return state["node"]

    def getNodeIds(self, state=None):
        state = self.getState(state)
        if "node" not in list(state.keys()):
            state["node"] = {}
        ids = list(state["node"].keys())
        ids.sort()
        return ids

    def getNetworks(self, state=None):
        state = self.getState(state)
        if "network" not in list(state.keys()):
            state["network"] = {}
        return state["network"]

    def getNetworkIds(self, state=None):
        state = self.getState(state)
        if "network" not in list(state.keys()):
            state["network"] = {}
        ids = list(state["network"].keys())
        ids.sort()
        return ids

    def getLinks(self, state=None):
        state = self.getState(state)
        if "link" not in list(state.keys()):
            state["link"] = {}
        return state["link"]

    def getLinkIds(self, state=None):
        state = self.getState(state)
        if "link" not in list(state.keys()):
            state["link"] = {}
        ids = list(state["link"].keys())
        ids.sort()
        return ids

    def getGlobal(self, state=None):
        state = self.getState(state)
        if "global" not in list(state.keys()):
            state["global"] = {}
        return state["global"]

    def getGlobalIsp(self, state=None):
        state = self.getIspState(state)
        if "global_isp" not in list(state.keys()):
            state["global_isp"] = {}
        return state["global_isp"]

# Retrieve Node interface information

    def getNode(self, node_id=None, state=None):
        if node_id is None:
            node_id = self.node_id
        if node_id not in self.getNodeIds(state):
            return {}
        nodes = self.getNodes(state)
        return nodes[node_id]

    def getNodeInterfaces(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "interface" not in list(node_record.keys()):
            return {}
        return node_record["interface"]

    def getNodeInterfaceIds(self, node_id=None, state=None):
        node_interfaces = self.getNodeInterfaces(node_id, state)
        return list(node_interfaces.keys())

    def getNodeInterface(self, interface_id, node_id=None, state=None):
        node_interfaces = self.getNodeInterfaces(node_id, state)
        if interface_id not in list(node_interfaces.keys()):
            return {}
        return node_interfaces[interface_id]

    def getNodeInterfaceType(self, interface_id, node_id=None, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface == {}:
            return ""
        return node_interface["type"]

    def getNodeInterfaceAddresses(self, interface_id, node_id=None, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface == {}:
            return []
        return list(node_interface["ip"].keys())

    def getNodeAddrMatchingPrefix(self, node_id, interface, prefix):
        """Each interface may have multiple addresses, this function will get addresses based on interface and prefix.

        Args:
           node_id (str): A string containing the node_id, example: "cloud", "BorderRouter"
           interface (str): A string containing interface id, example: "wpan0", "wlan0"
           prefix (str): A string containing an IP prefix, example: "10.0.1"

        Returns:
           addresses_matchPrefix: A string list containing IP addresses
        """
        addresses = self.getNodeInterfaceAddresses(interface, node_id)
        addresses_matchPrefix = []
        for address in addresses:
            if IP.prefixMatchAddress(prefix, address):
                addresses_matchPrefix.append(address)
        return addresses_matchPrefix

    def getNodeInterfaceAddressInfo(self, interface_id, addr, node_id=None, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface == {}:
            return {}
        if addr not in self.getNodeInterfaceAddresses(interface_id, node_id, state):
            return {}
        return node_interface["ip"][addr]

    def getNodeInterfaceAddressMask(self, interface_id, addr, node_id=None, state=None):
        node_address_info = self.getNodeInterfaceAddressInfo(interface_id, addr, node_id, state)
        if node_address_info == {}:
            return None
        return node_address_info["mask"]

    def getNodeInterfaceLinkId(self, interface_id, node_id=None, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface == {}:
            return []
        return node_interface["link"]

    def getNodeAddresses(self, node_id=None, state=None):
        node_interfaces = self.getNodeInterfaceIds(node_id, state)
        addrs = []
        for interface_id in node_interfaces:
            addr = self.getNodeInterfaceAddresses(interface_id, node_id, state)
            addrs += addr
        return addrs

    def getNodePublicIPv4Address(self, node_id=None, state=None):
        node_public_interfaces = self.getNodePublicInterfaces(node_id, state)
        for interface_id in node_public_interfaces:
            addresses = self.getNodeInterfaceAddresses(interface_id, node_id, state)
            for addr in addresses:
                if IP.isIpv4(addr):
                    return addr
        return None

    def getNodePublicInterfaces(self, node_id=None, state=None):
        public_interfaces = []
        node_interfaces = self.getNodeInterfaces(node_id, state)
        for interface_id in node_interfaces.keys():
            interface_type = self.getNodeInterfaceType(interface_id, node_id, state)
            if interface_type == self.network_type["wan"]:
                public_interfaces.append(interface_id)
        return public_interfaces

    def getNodeIdFromAddress(self, addr, state=None):
        for node_id in self.getNodeIds(state):
            node_addresses = self.getNodeAddresses(node_id, state)
            if addr in node_addresses:
                return node_id
        return None

    def getNodeInterfaceAddressMask(self, interface_id, addr, node_id=None, state=None):
        interface_addresses = self.getNodeInterfaceAddresses(interface_id, node_id, state)
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface == {}:
            return 0
        if addr not in interface_addresses:
            return 0
        return node_interface["ip"][addr]["mask"]

    def getNodeInterfacePrefixes(self, interface_id, node_id=None, state=None):
        if node_id is None:
            node_id = self.node_id
        if node_id is None:
            return []
        if node_id not in self.getNodeIds(state):
            return []
        if interface_id not in self.getNodeInterfaceIds(node_id, state):
            return []
        prefixes = []
        for addr in self.getNodeInterfaceAddresses(interface_id, node_id, state):
            mask = self.getNodeInterfaceAddressMask(interface_id, addr, node_id, state)
            prefix = IP.getPrefix(addr, mask)
            prefixes.append(prefix)
        return prefixes

    def getNodeRoutes(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "route" not in list(node_record.keys()):
            return {}
        return node_record["route"]

    def getNodeRoutePrefix(self, route_type, node_id=None, state=None):
        """
        getting node route prefix base on route type "v4" or "v6"
        """
        node_routes = self.getNodeRoutes(node_id, state)
        for node_route in node_routes.keys():
            if route_type in node_route:
                return node_routes[node_route]["prefix"]
        else:
            return None

    def getNodeRouteVia(self, route_type, node_id=None, state=None):
        """
        getting node route via node id base on route type "v4" or "v6"
        """
        node_routes = self.getNodeRoutes(node_id, state)
        for node_route in node_routes.keys():
            if route_type in node_route:
                return node_routes[node_route]["via"]
        else:
            return None

    def getNodeRouteIds(self, node_id=None, state=None):
        node_routes = self.getNodeRoutes(node_id, state)
        return list(node_routes.keys())

    def getNodeRoute(self, route_to, node_id=None, state=None):
        node_routes = self.getNodeRoutes(node_id, state)
        if route_to not in list(node_routes.keys()):
            return {}
        return node_routes[route_to]

    def getNodeLinkIds(self, node_id=None, state=None):
        node_interfaces = self.getNodeInterfaces(node_id, state)
        links = []
        for interface_id in node_interfaces.keys():
            link = node_interfaces[interface_id]["link"]
            if link is not None:
                links.append(link)
        links.sort()
        return links

    def getNodeLinkFromInterface(self, interface_id, node_id=None, state=None):
        for interface in self.getNodeInterfaceIds(node_id, state):
            if interface == interface_id:
                node_interface = self.getNodeInterface(interface_id, node_id, state)
                return node_interface["link"]
        return None

    def getNodeInterfaceFromLink(self, link_id, node_id=None, state=None):
        for interface_id in self.getNodeInterfaceIds(node_id, state):
            node_interface = self.getNodeInterface(interface_id, node_id, state)
            if node_interface["link"] == link_id:
                return interface_id
        return None

    def getNodeTmuxSessionIds(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "tmux" not in list(node_record.keys()):
            return []
        return list(node_record["tmux"].keys())

    def getNodeTmuxSession(self, session_id, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "tmux" not in list(node_record.keys()):
            return {}
        if session_id not in self.getNodeTmuxSessionIds(node_id, state):
            return {}
        return node_record["tmux"][session_id]

    def getNodeTmuxSessionUser(self, session_id, node_id=None, state=None):
        tmux_session = self.getNodeTmuxSession(session_id, node_id, state)
        if tmux_session == {}:
            return None
        if "run_as_user" in list(tmux_session.keys()):
            return tmux_session["run_as_user"]
        else:
            return None

    def getNodeProcesses(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "process" not in list(node_record.keys()):
            return {}
        return node_record["process"]

    def getNodeProcessIds(self, node_id=None, state=None):
        node_processes = self.getNodeProcesses(node_id, state)
        return list(node_processes.keys())

    def getNodeProcess(self, tag, node_id=None, state=None):
        node_processes = self.getNodeProcesses(node_id, state)
        if tag not in list(node_processes.keys()):
            return {}
        return node_processes[tag]

    def getNodeType(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "type" not in list(node_record.keys()):
            return None
        return node_record["type"]

    def getNodeProcessPID(self, tag=None, node_id=None, state=None):
        process_record = self.getNodeProcess(tag, node_id, state)
        if "pid" not in list(process_record.keys()):
            return None
        return process_record["pid"]

    def getNodeProcessCreateTime(self, tag=None, node_id=None, state=None):
        process_record = self.getNodeProcess(tag, node_id, state)
        if "create_time" not in list(process_record.keys()):
            return None
        return process_record["create_time"]

    def getNodeProcessOutputFile(self, tag=None, node_id=None, state=None):
        process_record = self.getNodeProcess(tag, node_id, state)
        if "out" not in list(process_record.keys()):
            return None
        return process_record["out"]

    def getNodeProcessStraceFile(self, tag=None, node_id=None, state=None):
        process_record = self.getNodeProcess(tag, node_id, state)
        if "strace" not in list(process_record.keys()):
            return None
        return process_record["strace"]

    def getNodeProcessCommand(self, tag=None, node_id=None, state=None):
        process_record = self.getNodeProcess(tag, node_id, state)
        if "command" not in list(process_record.keys()):
            return None
        return process_record["command"]

    def getNodeNetNS(self, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "netns" not in list(node_record.keys()):
            return None
        return node_record["netns"]

# Retrieve Node network information

    def getNetwork(self, network_id=None, state=None):
        if network_id is None:
            network_id = self.network_id
        if network_id not in self.getNetworkIds(state):
            return {}
        networks = self.getNetworks(state)
        return networks[network_id]

    def getNetworkNetNS(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "netns" not in list(network_record.keys()):
            return None
        return network_record["netns"]

    def getNodeNetworkIds(self, node_id=None, state=None):
        ids = []
        for link_id in self.getNodeLinkIds(node_id, state):
            link_record = self.getLink(link_id, state)
            if link_record != {}:
                ids.append(link_record["network"])
        ids.sort()
        return ids

    def getNodeInterfacesOnNetwork(self, network_id, node_id=None, state=None):
        network_links = self.getNetworkLinkIds(network_id, state)
        node_links = self.getNodeLinkIds(node_id, state)
        common_links = set.intersection(set(network_links), set(node_links))
        common_links = list(common_links)
        node_interfaces = []
        for interface_id in self.getNodeInterfaceIds(node_id, state):
            node_interface = self.getNodeInterface(interface_id, node_id, state)
            if node_interface["link"] in common_links:
                node_interfaces.append(interface_id)
        return node_interfaces

    def getNodeAddressesOnNetwork(self, network_id, node_id=None, state=None):
        addrs = []
        interfaces = self.getNodeInterfacesOnNetwork(network_id, node_id, state)
        for interface in interfaces:
            a = self.getNodeInterfaceAddresses(interface, node_id, state)
            addrs += a
            addrs.sort(key=len, reverse=True)
        return addrs

    def getNodeAddressesOnPrefix(self, prefix, node_id=None, state=None):
        addrs = self.getNodeAddresses(node_id, state)
        res = []
        for addr in addrs:
            if IP.prefixMatchAddress(prefix, addr):
                res.append(addr)
        return res

    def getNodeAddressesOnNetworkOnPrefix(self, network_id, prefix, node_id=None, state=None):
        addrs_on_network = self.getNodeAddressesOnNetwork(network_id, node_id, state)
        addrs_on_prefix = self.getNodeAddressesOnPrefix(prefix, node_id, state)
        addrs = list(set(addrs_on_network).intersection(addrs_on_prefix))
        return addrs

# Retrieve network interface information

    def getNetworkNodesIds(self, network_id=None, state=None):
        if network_id not in self.getNetworkIds(state):
            return []
        ids = []
        for link_id in self.getNetworkLinkIds(network_id, state):
            ids.append(self.getLinkNode(link_id, state))
        ids.sort()
        return ids

    def getNetworkLinks(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "interface" not in list(network_record.keys()):
            return {}
        return network_record["interface"]

    def getNetworkLinkIds(self, network_id=None, state=None):
        network_links = self.getNetworkLinks(network_id, state)
        ids = list(network_links.keys())
        ids.sort()
        return ids

    def getNetworkLink(self, interface_id, network_id=None, state=None):
        network_links = self.getNetworkLinks(network_id, state)
        if interface_id not in list(network_links.keys()):
            return {}
        return network_links[interface_id]

    def getNetworkType(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "type" not in list(network_record.keys()):
            return None
        return network_record["type"]

    def getNetworkState(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "state" not in list(network_record.keys()):
            return None
        return network_record["state"]

    def getNetworkPrefixRecords(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "prefix" not in list(network_record.keys()):
            return {}
        return network_record["prefix"]

    def getNetworkPrefixes(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "prefix" not in list(network_record.keys()):
            return []
        return list(network_record["prefix"].keys())

    def getNetworkPrefixMask(self, prefix, network_id=None, state=None):
        network_prefixes = self.getNetworkPrefixRecords(network_id, state)
        if prefix not in self.getNetworkPrefixes(network_id, state):
            return None
        if "mask" not in list(network_prefixes[prefix].keys()):
            return None
        return network_prefixes[prefix]["mask"]

    def getNetworkRoutes(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "route" not in list(network_record.keys()):
            return {}
        return network_record["route"]

    def getNetworkRouteIds(self, network_id=None, state=None):
        network_record = self.getNetwork(network_id, state)
        if "route" not in list(network_record.keys()):
            return []
        return list(network_record["route"].keys())

    def getNetworkRoute(self, route_to, network_id=None, state=None):
        network_routes = self.getNetworkRoutes(network_id, state)
        if route_to not in list(network_routes.keys()):
            return {}
        return network_routes[route_to]

# Retrieve Link information

    def getLink(self, link_id=None, state=None):
        if link_id is None:
            link_id = self.link_id
        if link_id not in self.getLinkIds(state):
            return {}
        links = self.getLinks(state)
        return links[link_id]

    def getLinkNode(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "node" not in list(link.keys()):
            return None
        return link["node"]

    def getLinkNetwork(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "network" not in list(link.keys()):
            return None
        return link["network"]

    def getLinkType(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "type" not in list(link.keys()):
            return None
        return link["type"]

    def getLinkNumber(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "number" not in list(link.keys()):
            return None
        return link["number"]

    def getLinkTap(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "tap" not in list(link.keys()):
            return None
        return link["tap"]

    def getLinkNodeEnd(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "node_end" not in list(link.keys()):
            return None
        return link["node_end"]

    def getLinkNetworkEnd(self, link_id=None, state=None):
        link = self.getLink(link_id, state)
        if "network_end" not in list(link.keys()):
            return None
        return link["network_end"]

    def getInternet(self, state=None):
        global_record = self.getGlobal(state)
        if "internet" not in list(global_record.keys()):
            return {}
        return global_record["internet"]

    def getIsp(self, state=None):
        global_isp_record = self.getGlobalIsp(state)
        if "isp" not in list(global_isp_record.keys()):
            return {}
        return global_isp_record["isp"]

    def getDNS(self, state=None):
        global_record = self.getGlobal(state)
        if "DNS" not in list(global_record.keys()):
            return None
        return global_record["DNS"]

    def getInternetHostLinkId(self, isp_id, state=None):
        internet_record = self.getInternet(state)
        if isp_id in list(internet_record.keys()) and "host_link" not in internet_record[isp_id]:
            return None
        return internet_record[isp_id]["host_link"]

    def getInternetNodeLinkId(self, isp_id, state=None):
        internet_record = self.getInternet(state)
        if isp_id in list(internet_record.keys()) and "node_link" not in internet_record[isp_id]:
            return None
        return internet_record[isp_id]["node_link"]

    def getInternetNodeId(self, isp_id, state=None):
        internet_record = self.getInternet(state)
        if isp_id in list(internet_record.keys()) and "node_id" not in internet_record[isp_id]:
            return None
        return internet_record[isp_id]["node_id"]

    def getInternetIspAddr(self, isp_id, state=None):
        internet_record = self.getInternet(state)
        if isp_id in list(internet_record.keys()) and "isp_addr" not in internet_record[isp_id]:
            return None
        return internet_record[isp_id]["isp_addr"]

    def getInternetIspIndex(self, isp_id, state=None):
        internet_record = self.getInternet(state)
        if isp_id in list(internet_record.keys()) and "isp_index" not in internet_record[isp_id]:
            return None
        return internet_record[isp_id]["isp_index"]

    def getIspAvailable(self, state=None):
        isp_record = self.getIsp(state)
        available_ip_pool = [s for s in isp_record if not s["occupy"]]
        return available_ip_pool

    def getIspAvailableIndex(self, state=None):
        isp_record = self.getIsp(state)
        available_ip_pool = [s for s in isp_record if not s["occupy"]]
        return int(available_ip_pool[0]['isp_index']) - 1

    def getIspAddr(self, index, state=None):
        isp_record = self.getIsp(state)
        if index >= len(isp_record) or index < 0:
            return None
        if "isp_addr" not in list(isp_record[index].keys()):
            return None
        return isp_record[index]["isp_addr"]

    def getIspHostLinkId(self, index, state=None):
        isp_record = self.getIsp(state)
        if index > len(isp_record) or index < 0:
            return None
        if "isp_host_end" not in list(isp_record[index].keys()):
            return None
        return isp_record[index]["isp_host_end"]

    def getIspNodeLinkId(self, index, state=None):
        isp_record = self.getIsp(state)
        if index >= len(isp_record) or index < 0:
            return None
        if "isp_node_end" not in list(isp_record[index].keys()):
            return None
        return isp_record[index]["isp_node_end"]

    def getIspIndex(self, index, state=None):
        isp_record = self.getIsp(state)
        if index >= len(isp_record) or index < 0:
            return None
        if "isp_index" not in list(isp_record[index].keys()):
            return None
        return isp_record[index]["isp_index"]

    def setNodeProcess(self, process, tag, node_id=None, state=None):
        node_record = self.getNode(node_id, state)
        if "process" not in list(node_record.keys()):
            node_record["process"] = {}
        node_record["process"][tag] = process

    def setLink(self, link_id, link, state=None):
        links = self.getLinks(state)
        if links is not None:
            links[link_id] = link

    def setLinkNetworkNodeHw(self, link_id, network_id, node_id, hw_addr, state=None):
        links = self.getLinks(state)
        if links is not None:
            if link_id not in list(links.keys()):
                links[link_id] = {}
            links[link_id]["network"] = network_id
            links[link_id]["node"] = node_id
            links[link_id]["fix_hw_addr"] = hw_addr

    def setNode(self, node_id, node, state=None):
        nodes = self.getNodes(state)
        if nodes is not None:
            nodes[node_id] = node

    def setNetwork(self, network_id, network, state=None):
        networks = self.getNetworks(state)
        if networks is not None:
            networks[network_id] = network

    def setNodeIpAddress(self, node_id, interface_id, ip_address, record, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if node_interface is not None:
            if "ip" not in list(node_interface.keys()):
                node_interface["ip"] = {}
            node_interface["ip"][ip_address] = record

    def setNodeTmux(self, node_id, session_id, record, state=None):
        node_record = self.getNode(node_id, state)
        if "tmux" not in list(node_record.keys()):
            node_record["tmux"] = {}
        node_record["tmux"][session_id] = record

    def setNodeInterface(self, node_id, interface_id, record, state=None):
        node_record = self.getNode(node_id, state)
        if node_record is not None:
            node_record["interface"][interface_id] = record

    def setNodeRoute(self, node_id, to, record, state=None):
        node_record = self.getNode(node_id, state)
        if node_record is not None:
            if "route" not in list(node_record.keys()):
                node_record["route"] = {}

            if ("via" in list(record.keys()) and IP.isIpv6(record["via"])) or \
               ("prefix" in list(record.keys()) and IP.isIpv6(record["prefix"])):
                to = to + "_v6"
            else:
                to = to + "_v4"

            node_record["route"][to] = record

    def setNetworkState(self, network_id, network_state, state=None):
        network_record = self.getNetwork(network_id, state)
        if network_record is not None:
            network_record["state"] = network_state

    def setNetworkLink(self, network_id, link_id, record, state=None):
        network_record = self.getNetwork(network_id, state)
        if network_record is not None:
            network_record["interface"][link_id] = record

    def setNetworkRoute(self, network_id, to, record, state=None):
        network_record = self.getNetwork(network_id, state)
        if network_record is not None:
            if "route" not in list(network_record.keys()):
                network_record["route"] = {}

            if ("via" in list(record.keys()) and IP.isIpv6(record["via"])) or \
               ("prefix" in list(record.keys()) and IP.isIpv6(record["prefix"])):
                to = to + "_v6"
            else:
                to = to + "_v4"

            network_record["route"][to] = record

    def setNetworkPrefix(self, network_id, prefix, record, state=None):
        network_record = self.getNetwork(network_id, state)
        if network_record is not None:
            if "prefix" not in list(network_record.keys()):
                network_record["prefix"] = {}
            network_record["prefix"][prefix] = record

    def setGlobalInternet(self, record, state=None):
        global_record = self.getGlobal(state)
        global_record["internet"] = record

    def setGlobalIsp(self, record, state=None):
        global_isp_record = self.getGlobalIsp(state)
        global_isp_record["isp"] = record

    def setIspOccupancy(self, index, value, state=None):
        isp_record = self.getIsp(state)
        if index >= len(isp_record) or index < 0:
            return None
        isp_record[index]["occupy"] = value

    def setGlobalDNS(self, record, state=None):
        global_record = self.getGlobal(state)
        global_record["DNS"] = record

    def renameNode(self, node_id, new_node_id, state=None):
        nodes = self.getNodes(state)
        if nodes is not None:
            node_record = self.getNode(node_id, state)
            if node_record is not None:
                nodes[new_node_id] = node_record
                self.removeNode(node_id)

    def removeLink(self, link_id, state=None):
        links = self.getLinks(state)
        if link_id in self.getLinkIds(state):
            del links[link_id]

    def removeNode(self, node_id, state=None):
        nodes = self.getNodes(state)
        if node_id in self.getNodeIds(state):
            del nodes[node_id]

    def removeNodeNetNsMap(self, node_id, state=None):
        netns = self.getNetNS(state)
        if node_id in self.getNetNSIds(state):
            del netns[node_id]

    def removeIdentifiersMap(self, node_id, state=None):
        identifiers = self.getIdentifiers(state)
        identifier = self.getIdentifierByNodeId(node_id)
        if identifier in identifiers:
            del identifiers[identifier]

    def removeNetwork(self, network_id, state=None):
        networks = self.getNetworks(state)
        if network_id in self.getNetworkIds(state):
            del networks[network_id]

    def removeNodeInterface(self, node_id, interface_id, state=None):
        node_interfaces = self.getNodeInterfaces(node_id, state)
        if interface_id in self.getNodeInterfaceIds(node_id, state):
            del node_interfaces[interface_id]

    def removeNodeTmux(self, node_id, session_id, state=None):
        node_record = self.getNode(node_id, state)
        if "tmux" in list(node_record.keys()):
            if session_id in list(node_record["tmux"].keys()):
                del node_record["tmux"][session_id]

    def removeNodeRoute(self, node_id, to, state=None):
        node_record = self.getNode(node_id, state)
        if "route" in list(node_record.keys()):
            if to in list(node_record["route"].keys()):
                del node_record["route"][to]

    def removeNodeInterfaceAddress(self, node_id, interface_id, ip_address, state=None):
        node_interface = self.getNodeInterface(interface_id, node_id, state)
        if ip_address in self.getNodeInterfaceAddresses(interface_id, node_id, state):
            del node_interface["ip"][ip_address]

    def removeNetworkLink(self, network_id, link_id, state=None):
        network_links = self.getNetworkLinks(network_id, state)
        if link_id in self.getNetworkLinkIds(network_id, state):
            del network_links[link_id]

    def removeNetworkRoute(self, network_id, to, state=None):
        network_record = self.getNetwork(network_id, state)
        if "route" in list(network_record.keys()):
            if to in list(network_record["route"].keys()):
                del network_record["route"][to]

    def removeNetworkPrefix(self, network_id, prefix, state=None):
        network_record = self.getNetwork(network_id, state)
        if "prefix" in list(network_record.keys()):
            if prefix in list(network_record["prefix"].keys()):
                del network_record["prefix"][prefix]

    def removeGlobalInternet(self, isp_id, state=None):
        global_record = self.getGlobal(state)
        if "internet" in list(global_record.keys()) and isp_id in list(global_record['internet'].keys()):
            del global_record["internet"][isp_id]
        if not bool(global_record['internet']):
            del global_record["internet"]

    def removeGlobalIsp(self, state=None):
        global_record = self.getGlobalIsp(state)
        if "isp" in list(global_record.keys()):
            del global_record["isp"]

    def removeGlobalDNS(self, state=None):
        global_record = self.getGlobal(state)
        if "DNS" in list(global_record.keys()):
            del global_record["DNS"]

    def getExtensionState(self, state=None):
        """
        return a list of states created by happy plugins,
        "weave" is one of the extension created by happy plugins.
        """
        knownStateKeys = set(['identifiers', 'link', 'node', 'netns', 'network'])
        state = self.getState(state)
        filteredState = dict([i for i in six.iteritems(state) if i[0] not in knownStateKeys])
        return filteredState

    def getNodeInfo(self, node, state=None, happy_only=False):
        """
        get all information of a node
        happy_only: only display happy states, not including extension states like weave
        """
        happy_node_info = self.getNodes()[node]
        node_info = {"happy": happy_node_info}

        # get extension state including weave
        if not happy_only:
            for i in six.iteritems(self.getExtensionState(state)):
                extState = self.getNodes(i[1])
                if extState and node in extState:
                    node_info[i[0]] = extState[node]

        return node_info

    def getExtensionValue(self, extension_name, state=None):
        """
        extension_name example: weave-fabric-id
        """
        ext_look_list = extension_name.split("-")
        ext_states = self.getExtensionState(state)
        for item in ext_look_list:
            if item not in ext_states:
                return None
            else:
                ext_states = ext_states[item]
                ext_value = ext_states
        return ext_value

    def IsTapDevice(self, node_id, state=None):
        """
        check if a device is a tap device or not
        if tap device, will not call netns command to add route
        1. get links of a node
        2. verify link is TAP or not
        Happy only support one interface type now,
        it is either tap device or regular linux socket device
        """
        node_links = self.getNodeLinkIds(node_id)
        # no link_id for cloud node service-tun0 interface
        if None in node_links:
            node_links.remove(None)
        for link in node_links:
            if self.getLinkTap(link):
                return True
        else:
            return False
