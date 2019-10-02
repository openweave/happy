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
#       Implements HappyInternet class through which a virtual node connects to the
#       internet through a virtual ISP.
#
#

import os
import sys
import json
import time

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
from happy.HappyNodeRoute import HappyNodeRoute

options = {}
options["quiet"] = False
options["node_id"] = None
options["iface"] = None
options["add"] = False
options["delete"] = False
options["isp"] = None
options["seed"] = None


def option():
    return options.copy()


class HappyInternet(HappyNode, HappyNodeRoute):
    """
    Connects a virtual node to the internet through a virtual ISP.

    happy-internet [-h --help] [-q --quiet] [-a --add] [-d --delete]
                   [-n --node <NODE_NAME>] [-f --interface <IFACE>] [-s --isp <ISP>]
                   [-e --seed <SEED>]

        -d --delete     Disconnect the topology from the internet. Use the same
                        configuration (interface, isp, seed) as when it was connected.
        -f --interface  Interface that provides default internet connectivity to the host.
        -s --isp        User-defined string to be used for the ISP name.
        -e --seed       Seed value used in the host IP prefix of 172.16.<seed>.1
                        Range: 1-252

    Examples:
    $ happy-internet --node onhub --interface eth0 --isp eth --seed 249
        Connects virtual node onhub to the internet through the host's eth0 interface.

    $ happy-internet -d --interface eth0 --isp eth --seed 249
        Disconnects the topology from the internet.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)
        HappyNodeRoute.__init__(self)
        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.add = opts["add"]
        self.delete = opts["delete"]
        self.iface = opts["iface"]
        self.isp_id = opts["isp"]
        self.seed = int(opts["seed"])
        self.prefix = '172.16.' + opts["seed"] + '.'
        self.mask = "24"
        self.host_addr = self.prefix + "1"
        self.isp_internet_id = self.isp_id + "1"
        self.bridge = self.isp_id + 'Bridge'
        self.isp_pool = None
        self.init_happy_isp(isp_id=(self.isp_id + '_'))

        self.iptable_rules = list()

    def __pre_check(self):
        if isinstance(self.seed, int) and not (0 < self.seed < 253):
            emsg = "seed %s is not in range[1, 252]" % self.seed
            self.logger.error("HappyInternet: %s" % emsg)
            sys.exit(1)

        if not self.delete:
            self.add = True

        if self.delete:
            self.node_id = self.getInternetNodeId(isp_id=self.isp_id)
            if not self.node_id:
                emsg = "there is no node connected to the Internet."
                self.logger.error("[localhost] HappyInternet: %s" % (emsg))
                sys.exit(1)

            self.isp_addr = self.getInternetIspAddr(isp_id=self.isp_id)

            if not self.isp_addr:
                emsg = "virtual node %s does not have isp IP address." % (self.isp_addr)
                self.logger.error("[%s] HappyInternet: %s" % (self.isp_addr, emsg))
                sys.exit(1)

            self.isp_index = self.getInternetIspIndex(isp_id=self.isp_id)

            if not self.isp_index:
                emsg = "virtual node %s does not have isp index assigned from virtual ISP." % (self.isp_index)
                self.logger.error("[%s] HappyInternet: %s" % (self.isp_index, emsg))
                sys.exit(1)

            self.isp_node_end = self.getInternetNodeLinkId(isp_id=self.isp_id)

            if not self.isp_node_end:
                emsg = "virtual node %s does not have isp node link." % (self.isp_node_end)
                self.logger.error("[%s] HappyInternet: %s" % (self.isp_node_end, emsg))
                sys.exit(1)

            self.isp_host_end = self.getInternetHostLinkId(isp_id=self.isp_id)
            if not self.isp_host_end:
                emsg = "virtual node %s does not have isp host link to isp." % (self.isp_host_end)
                self.logger.error("[%s] HappyInternet: %s" % (self.isp_host_end, emsg))
                sys.exit(1)

        # Check if the name of the node is given
        if self.add and not self.node_id:
            emsg = "Missing name of the virtual node that should connect to the Internet."
            self.logger.error("[localhost] HappyInternet: %s" % (emsg))
            sys.exit(1)

        # Check if node exists
        if not self._nodeExists():
            emsg = "virtual node %s does not exist." % (self.node_id)
            self.logger.error("[%s] HappyInternet: %s" % (self.node_id, emsg))
            sys.exit(1)

        # Check if already connected to internet
        if self.add and self.isp_id in self.getInternet():
            emsg = "virtual node %s is connected to the Internet." % (self.getInternetNodeId(isp_id=self.isp_id))
            self.logger.error("[%s] HappyInternet: %s" % (self.getInternetNodeId(isp_id=self.isp_id), emsg))
            sys.exit(1)

        # Check if node is a host (local)
        if self.add and self.isNodeLocal(self.node_id):
            emsg = "Host node should be already connected to the Internet."
            self.logger.error("[localhost] HappyInternet: %s" % (emsg))
            self.exit()

    def __get_internet_interface_info(self):
        # set marchine's internet veth link naming
        self.internet_host_end = self.isp_internet_id + "_host"
        self.internet_node_end = self.isp_internet_id + "_node"

    def __initialize_isp_pool(self):
        # initialize isp pool
        isp_seed = range(1, 256)
        self.isp_pool = [{"isp_addr": self.prefix + str(i),
                          "isp_index": str(i),
                          "occupy": False,
                          "isp_host_end": self.isp_id + str(i) + "_host",
                          "isp_node_end": self.isp_id + str(i) + "_node"} for i in isp_seed]
        self.setGlobalIsp(self.isp_pool)

    def __get_isp_from_pool(self):
        # get isp from pool
        index = self.getIspAvailableIndex()
        self.isp_host_end = self.getIspHostLinkId(index=index)
        self.isp_node_end = self.getIspNodeLinkId(index=index)
        self.isp_addr = self.getIspAddr(index=index)
        self.isp_index = self.getIspIndex(index=index)
        self.setIspOccupancy(index=index, value=True)

    def __release_isp_to_pool(self):
        # release isp to pool
        self.setIspOccupancy(index=int(self.isp_index) - 1, value=False)

    def __create_isp_internet_link(self):
        # init machine's isp internet link
        cmd = "ip link add name " + self.internet_node_end + " type veth peer name " + self.internet_host_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __create_isp_link(self):
        # init node's isp link
        cmd = "ip link add name " + self.isp_node_end + " type veth peer name " + self.isp_host_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __delete_isp_internet_link(self):
        # delete machine's isp internet link
        cmd = "ip link delete " + self.internet_node_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __create_isp(self):
        # create isp
        cmd = "ip netns add %s" % self.bridge
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip netns exec %s brctl addbr %s" % (self.bridge, self.bridge)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip netns exec %s brctl setageing %s 0" % (self.bridge, self.bridge)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip netns exec %s ifconfig %s up" % (self.bridge, self.bridge)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __connect_internet_to_isp(self):
        # link machine's internet link to happy_isp
        cmd = "ip link set " + self.internet_host_end + " netns %s" % self.bridge
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip netns exec %s brctl addif %s " % (self.bridge, self.bridge) + self.internet_host_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)
        self.setIspOccupancy(index=0, value=True)

    def __connect_node_to_isp(self):
        # link node's internet link to happy_isp
        cmd = "ip link set " + self.isp_host_end + " netns %s" % self.bridge
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip link set " + self.isp_node_end + " netns " + self.uniquePrefix(self.node_id)
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        cmd = "ip netns exec %s brctl addif %s " % (self.bridge, self.bridge) + self.isp_host_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __nmconf(self):
        # configure nmcli
        tries = 3
        state = self.getHostNMInterfaceStatus(self.internet_node_end)

        if state is None:
            return
        elif state == "unmanaged":
            cmd = "nmcli dev set {} managed yes".format(self.internet_node_end)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)
            state = self.getHostNMInterfaceStatus(self.internet_node_end)

        while tries > 0:
            if state == "connecting":
                break
            time.sleep(1)
            state = self.getHostNMInterfaceStatus(self.internet_node_end)
            tries -= 1
        else:
            emsg = "Failed to setup host interface {} with nmcli. Internet may not working.".format(
                self.internet_node_end)
            self.logger.warning("[localhost] HappyInternet: {}".format(emsg))
            return

        cmd = "nmcli dev disconnect " + self.internet_node_end
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def __ctrl_isp_internet_interface(self):
        # configure internet veth link in both isp and host sides
        if self.add:
            cmd = "ip netns exec %s ifconfig " % self.bridge + self.internet_host_end + " up"
        else:
            cmd = "ip netns exec %s ifconfig " % self.bridge + self.internet_host_end + " down"

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        if self.add:
            cmd = "ifconfig " + self.internet_node_end + " up"
        else:
            cmd = "ifconfig " + self.internet_node_end + " down"

        cmd = self.runAsRoot(cmd)
        r = self.CallAtHost(cmd)

    def __ctrl_isp_node_interface(self):
        # configure isp veth link in both isp and node sides
        if self.add:
            cmd = "ifconfig " + self.isp_node_end + " up"
        else:
            cmd = "ifconfig " + self.isp_node_end + " down"

        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(self.node_id, cmd)

        if self.add:
            cmd = "ip netns exec %s ifconfig " % self.bridge + self.isp_host_end + " up"
        else:
            cmd = "ip netns exec %s ifconfig " % self.bridge + self.isp_host_end + " down"

        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        if not self.add:
            cmd = "ip link delete " + self.isp_node_end
            cmd = self.runAsRoot(cmd)
            r = self.CallAtNode(self.node_id, cmd)

    def __internet_state(self):
        # update the internet status in node per happy instance
        if self.add:
            internet = self.getInternet()
            isp_dic = {}
            isp_dic["node_link"] = self.isp_node_end
            isp_dic["host_link"] = self.isp_host_end
            isp_dic["isp_addr"] = self.isp_addr
            isp_dic["node_id"] = self.node_id
            isp_dic["isp_index"] = self.isp_index
            isp_dic["isp"] = self.isp_id
            isp_dic["iface"] = self.iface
            internet[self.isp_id] = isp_dic
            self.setGlobalInternet(internet)
        else:
            self.removeGlobalInternet(isp_id=self.isp_id)

    def __assign_isp_internet_address(self):
        # assign isp address in host side
        cmd = "ip address add " + self.host_addr + "/" + self.mask + " dev " + self.internet_node_end
        cmd = self.runAsRoot(cmd)
        r = self.CallAtHost(cmd)

    def __assign_isp_address(self):
        # assign isp address in node side
        cmd = "ip address add " + self.isp_addr + "/" + self.mask + " dev " + self.isp_node_end
        cmd = self.runAsRoot(cmd)
        r = self.CallAtNode(self.node_id, cmd)

    def __route(self):
        if self.nodeIpv4DefaultExist(self.node_id):
            # configure ip route table
            table = self.isp_id + "_table"
            if self.add:
                self.rt_table_update(priority=self.seed, table_id=table, node=self.node_id)
                self.add_route_rule(addr=self.isp_addr, table=table, via_address=self.host_addr,
                                    interface=self.isp_node_end, node=self.node_id)
            else:
                self.remove_route_rule(table=table, node=self.node_id)
                cmd = "ip route delete default"
                cmd = self.runAsRoot(cmd)
                r = self.CallAtNode(self.node_id, cmd)
        else:
            if self.add:
                cmd = "ip route add default via " + self.host_addr
                cmd = self.runAsRoot(cmd)
                r = self.CallAtNode(self.node_id, cmd)

    def __nat_host(self):
        # If interface is not provided, try guessing one
        if not self.iface:
            if "happy_host_netif" in os.environ.keys():
                self.iface = os.environ['happy_host_netif']
            else:
                self.iface = self.getDefaultInterfaceName()

            emsg = "Connecting to Internet through interface %s." % (self.iface)
            self.logger.debug("[localhost] HappyInternet: %s" % (emsg))
        # Check if interface is provided
        if self.add and not self.iface:
            emsg = "Missing name the host computer network interface that is connected to the Internet."
            self.logger.error("[localhost] HappyInternet: %s" % (emsg))
            self.exit()

        # configure nat on host
        status = 1 if self.add else 0

        cmd = "sysctl -n -w net.ipv6.conf.all.forwarding=%d" % (status)
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtHostForOutput(cmd)

        cmd = "sysctl -n -w net.ipv4.ip_forward=%d" % (status)
        cmd = self.runAsRoot(cmd)
        out, err = self.CallAtHostForOutput(cmd)

        if self.delete:
            return

        # Post routing on host
        iptable_cmd_list = [
            "POSTROUTING -o {} -j MASQUERADE".format(self.iface),
            "FORWARD -i {} -o {} -m state --state RELATED,ESTABLISHED -j ACCEPT".format(self.iface,
                                                                                        self.internet_node_end),
            "FORWARD -i {} -o {} -j ACCEPT".format(self.internet_node_end, self.iface)
        ]
        for rule in iptable_cmd_list:
            table = "-t filter"
            if any(keyword in rule for keyword in ('POSTROUTING', 'PREROUTING')):
                table = "-t nat"
            # Checking if rule exists
            cmd = "iptables {} -C {}".format(table, rule)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)
            if not ret:
                self.logger.info("iptables rule exists..do nothing..")
                self.iptable_rules.append(rule)
                continue
            # Add iptable rule
            cmd = "iptables {} -A {}".format(table, rule)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)
            if ret:
                _, err = self.CallAtHostForOutput(cmd)
                raise Exception("Unable to add iptable rule: \nErr: {}".format(err))

            self.iptable_rules.append(rule)

    def __nat_isp_node(self):
        # configure nat on node
        # Post routing on node
        iptable_cmd_list = [
            "POSTROUTING -o {} -j MASQUERADE".format(self.isp_node_end),
            "FORWARD -o {} -m state --state RELATED,ESTABLISHED -j ACCEPT".format(self.isp_node_end),
            "FORWARD -i {} -j ACCEPT".format(self.isp_node_end)
        ]
        for rule in iptable_cmd_list:
            table = "-t filter"
            if any(keyword in rule for keyword in ('POSTROUTING', 'PREROUTING')):
                table = "-t nat"
            cmd = "iptables {} -A {}".format(table, rule)
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtNode(self.node_id, cmd)

    def __save_iptable_commands(self):
        """
        API to save successfully executed iptable rules for later restore back to
        origin iptable settings.
        """
        if not len(self.iptable_rules):
            self.logger.warn("iptable: Nothing to be save, "
                             "please check and see if that is correct.")
            return
        isp_state_dict = json.load(open(self.isp_state_file, 'r'))
        isp_state_dict.update({"isp_state_fw": self.iptable_rules})
        with open(self.isp_state_file, 'w') as fp:
            json.dump(isp_state_dict, fp)

    def __flush_iptable_commands(self):
        """API to remove iptable rules that is create by happy"""
        if not os.path.isfile(self.isp_state_file):
            self.logger.warn("Unable to run iptable rules flush, isp state file is missing."
                             "Do nothing..")
            return

        with open(self.isp_state_file, 'r') as fp:
            fw_dict = json.load(fp).get("isp_state_fw", None)
            if not fw_dict:
                self.logger.warn("No added firewall rules need to be flush. "
                                 "Do nothing...")
                return
            for rule in fw_dict:
                table = "-t filter"
                if any(keyword in rule for keyword in ('POSTROUTING', 'PREROUTING')):
                    table = "-t nat"
                cmd = "iptables {} -C {}".format(table, rule)
                cmd = self.runAsRoot(cmd)
                while not self.CallAtHost(cmd):
                    cmd1 = "iptables {} -D {}".format(table, rule)
                    cmd1 = self.runAsRoot(cmd1)
                    ret = self.CallAtHost(cmd1)

    def __delete_isp(self):
        # delete isp network namespace
        cmd = "ip netns del %s" % self.bridge
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

    def run(self):
        self.__pre_check()
        self.__get_internet_interface_info()

        if self.add:
            with self.getStateLockManager(lock_id="isp"):
                self.readIspState()
                # print self.getStateId()
                self.isp_pool = self.getIsp()
                if not bool(self.isp_pool):
                    self.__initialize_isp_pool()
                    self.__create_isp_internet_link()
                    self.__create_isp()
                    self.__connect_internet_to_isp()
                    self.__ctrl_isp_internet_interface()
                    self.__nmconf()
                    self.__assign_isp_internet_address()
                    self.__nat_host()
                self.__get_isp_from_pool()
                self.writeIspState()
            self.__create_isp_link()
            self.__connect_node_to_isp()
            self.__assign_isp_address()
            self.__ctrl_isp_node_interface()
            with self.getStateLockManager(lock_id="rt"):
                self.__route()
            self.__nat_isp_node()
            self.__save_iptable_commands()
            with self.getStateLockManager():
                self.__internet_state()
                self.writeState()

        if self.delete:
            with self.getStateLockManager():
                self.__route()
                self.__internet_state()
                self.writeState()

            self.__ctrl_isp_node_interface()
            with self.getStateLockManager(lock_id="isp"):
                self.readIspState()

                self.__release_isp_to_pool()
                if len(self.getIspAvailable()) == 254:
                    self.__ctrl_isp_internet_interface()
                    self.__delete_isp_internet_link()
                    self.__delete_isp()
                    self.removeGlobalIsp()

                self.writeIspState()
            self.__flush_iptable_commands()

        return ReturnMsg(0)
