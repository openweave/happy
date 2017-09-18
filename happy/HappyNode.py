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
#       Implements HappyNode class that provides virtual nodes abstraction.
#
#       virtual node specific actions inherit from this class.
#

import os
import sys

from happy.Utils import *
from happy.HappyHost import HappyHost
import happy.HappyLinkDelete


class HappyNode(HappyHost):
    def __init__(self, node_id=None):
        HappyHost.__init__(self)

        self.node_id = node_id

        self.node_type_ap = "ap"
        self.node_type_local = "local"
        self.node_type_service = "service"

        self.node_special_type = {}
        self.node_special_type["ap"] = {}
        self.node_special_type["ap"]["description"] = "access point"
        self.node_special_type["service"] = {}
        self.node_special_type["service"]["description"] = "nest service"
        self.node_special_type["local"] = {}
        self.node_special_type["local"]["description"] = "local host computer"
        self.nsroot = "/etc/netns"

    def _nodeExists(self, node_id=None):
        if node_id is None:
            node_id = self.node_id

        if self.isNodeLocal(node_id):
            return node_id in self.getNodeIds()
        else:
            return self._namespaceExists(node_id)

    def getNodeInterfaceName(self, node_id, type):
        interface_base_name = self.typeToName(self.link_type)
        interface_number = 0
        for interface_id in self.getNodeInterfaceIds(node_id):
                node_interface = self.getNodeInterface(interface_id, node_id)
                if node_interface["type"] == self.link_type:
                    interface_number += 1

        interface_full_name = interface_base_name + str(interface_number)

        if self.getNodeType(node_id) == "local":
            while interface_full_name in self.getHostInterfaces():
                interface_number += 1
                interface_full_name = interface_base_name + str(interface_number)

        return interface_full_name

    def _nodeInterfaceExists(self, interface_id, node_id=None):
        interfaces = self.getActiveNodeLinks(node_id)
        if len(interfaces) == 0 or interface_id not in interfaces:
            return False
        return True

    def DeleteNodeInterfaces(self):
        interfaces = self.getNodeInterfaces()
        for interface_id in interfaces.keys():
            link_id = self.getNodeInterfaceLinkId(interface_id)
            if link_id is not None:
                self._delete_node_link(link_id)

    def _delete_node_link(self, link_id):
        options = happy.HappyLinkDelete.option()
        options["quiet"] = self.quiet
        options["link_id"] = link_id
        cmd = happy.HappyLinkDelete.HappyLinkDelete(options)
        ret = cmd.run()

        self.readState()

    def delete_node_from_network(self, network_id):
        network_link_ids = self.getNetworkLinkIds(network_id)
        node_link_ids = self.getNodeLinkIds()

        links_to_delete = list(set(network_link_ids).intersection(node_link_ids))

        for link_id in links_to_delete:
            self._delete_node_link(link_id)

    def getIpAddressesRecords(self, interface_id=None, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "ip addr show"
        if interface_id is not None:
            cmd += " " + interface_id

        out, err = self.CallAtNodeForOutput(node_id, cmd)
        return out

    def getIpAddresses(self, interface_id=None, node_id=None):
        out = self.getIpAddressesRecords(interface_id, node_id)

        ipaddrs = []

        for line in out.split("\n"):
            l = line.split()
            if len(l) < 4:
                continue

            if l[0][:4] == "inet":
                addr = l[1]
                addr, mask = addr.split("/")
                addr = self.paddingZeros(addr)
                ipaddrs.append(addr)

        return ipaddrs

    def getIpAddressStatus(self, address, interface_id=None, node_id=None):
        out = self.getIpAddressesRecords(interface_id, node_id)

        for line in out.split("\n"):
            l = line.split()
            if l[0][:4] == "inet":
                addr = l[1]
                addr, mask = addr.split("/")
                addr = self.paddingZeros(addr)
                if addr != address:
                    continue

                print line
                return line

        return None

    def getHwAddress(self, interface_id=None, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "ip addr show"
        if interface_id is not None:
            cmd += " " + interface_id

        out, err = self.CallAtNodeForOutput(node_id, cmd)

        for line in out.split("\n"):
            l = line.split()
            if len(l) < 4:
                continue

            if l[0][:4] == "link":
                return l[1]

        return None

    def getInterfaceEUI64(self, interface_id, node_id=None):
        eui = None
        node_interface = self.getNodeInterface(interface_id, node_id)
        if "customized_eui64" in node_interface.keys():
            eui = str(node_interface["customized_eui64"])
        else:
            hwAddr = self.getHwAddress(interface_id, node_id)

            if hwAddr is not None:
                eui = self.MAC48toEUI64(hwAddr)

        return eui

    def getInterfaceId(self, interface_id, node_id=None):
        eui = self.getInterfaceEUI64(interface_id, node_id)

        if eui is None:
            return None

        iid = self.EUI64toIID(eui)
        return iid

    def getNodeAddressOnPrefix(self, prefix, id):
        if self.isIpv6(prefix):
            return self.__getNodeIPv6AddressOnPrefix(prefix, id)
        else:
            return self.__getNodeIPv4AddressOnPrefix(prefix, id)

    def __getNodeIPv6AddressOnPrefix(self, prefix, id):
        prefix_addr, prefix_mask = self.splitAddressMask(prefix)

        addr = prefix_addr + "::" + id

        if addr.count(":") == 8:
            addr = addr.replace("::", ":")

        addr = self.paddingZeros(addr)

        return addr

    def __getNodeIPv4AddressOnPrefix(self, prefix, id):
        prefix_addr, prefix_mask = self.splitAddressMask(prefix)
        prefix_mask = int(float(prefix_mask))

        addr = prefix_addr.split(".")[:prefix_mask / 8]
        addr.append(str(id % 255))

        addr = ".".join(addr)

        return addr

    def fixHwAddr(self, addr):
        if addr is None:
            return addr

        addr = addr.split(":")

        for i in range(len(addr)):
            if len(addr[i]) == 1:
                addr[i] = "0" + addr[i]

        addr = ":".join(addr)

        while addr.count(":") < 5:
            addr = "00:" + addr

        return addr

    def nodeIPv6Forwarding(self, status=None, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "sysctl -n net.ipv6.conf.all.forwarding"
        if status is not None and status in [0, 1]:
            cmd = "sysctl -n -w net.ipv6.conf.all.forwarding=%d" % (status)

        out, err = self.CallAtNodeForOutput(node_id, cmd)
        return int(float(out))

    def nodeIPv4Forwarding(self, status=None, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "sysctl -n net.ipv4.ip_forward"
        if status is not None and status in [0, 1]:
            cmd = "sysctl -n -w net.ipv4.ip_forward=%d" % (status)

        out, err = self.CallAtNodeForOutput(node_id, cmd)
        return int(float(out))

    def setNATonInterface(self, interface_id, node_id=None):
        if node_id is None:
            node_id = self.node_id

        cmd = "iptables -t nat -A POSTROUTING -o " + interface_id + " -j MASQUERADE"
        ret = self.CallAtNode(node_id, cmd)

        for other_interface in self.getNodeInterfaceIds(node_id):
            if other_interface == interface_id:
                continue

            cmd = "iptables -A FORWARD -i " + interface_id + " -o " + other_interface + \
                  " -m state --state RELATED,ESTABLISHED -j ACCEPT"
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtNode(node_id, cmd)

            cmd = "iptables -A FORWARD -i " + other_interface + " -o " + interface_id + \
                  " -j ACCEPT"
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtNode(node_id, cmd)
