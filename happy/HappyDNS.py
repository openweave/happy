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
#       Implements HappyDNS class through which nodes get DNS name servers.
#
#

import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["add"] = False
options["delete"] = False
options["dns"] = None
options["node_id"] = None


def option():
    return options.copy()


class HappyDNS(HappyNode):
    """
    happy-dns provides DNS nameservers to virtual nodes.

    happy-dns [-h --help] [-q --quiet] [-a --add] [-d --delete]
                [-i --id <NODE_NAME>] <DNS_LIST>

    Example:
    $ happy-dns 111.222.333.444
        assign to all virtual nodes DNS server 111.222.333.444

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.add = opts["add"]
        self.delete = opts["delete"]
        self.dns = opts["dns"]
        self.node_id = opts["node_id"]

    def __pre_check(self):
        if not self.delete:
            self.add = True

        if not self.dns:
            if "happy_dns" in os.environ.keys():
                self.dns = os.environ['happy_dns'].split()

        if self.add and self.dns is None:
            emsg = "No DNS servers listed."
            self.logger.error("[localhost] HappyDNS: %s" % (emsg))
            self.exit()

        for dns_addr in self.dns:
            if not self.isIpv4(dns_addr):
                emsg = "DNS %s is not a valid IPv4 address." % (dns_addr)
                self.logger.error("[localhost] HappyDNS: %s" % (emsg))
                self.exit()

    def __add_node_dns(self, node_id):
        nspath = self.nsroot + "/" + self.uniquePrefix(node_id)
        resolv_path = nspath + "/" + "resolv.conf"

        if not os.path.isdir(nspath):
            cmd = "mkdir -p " + nspath
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

        if not os.path.exists(resolv_path):
            cmd = "touch " + resolv_path
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

        cmd = "chmod 666 " + resolv_path
        cmd = self.runAsRoot(cmd)
        ret = self.CallAtHost(cmd)

        with open(resolv_path, 'w') as res:
            for dns_addr in self.dns:
                line = "nameserver " + dns_addr + "\n"
                res.write(line)

    def __remove_node_dns(self, node_id):
        nspath = self.nsroot + "/" + self.uniquePrefix(node_id)
        resolv_path = nspath + "/" + "resolv.conf"
        if os.path.exists(resolv_path):
            cmd = "rm " + resolv_path
            cmd = self.runAsRoot(cmd)
            ret = self.CallAtHost(cmd)

    def __update_nodes_dns(self):
        if self.node_id:
            nodes = [self.node_id]
        else:
            nodes = self.getNodeIds()

        for node_id in nodes:
            if self.add:
                self.__add_node_dns(node_id)
            else:
                self.__remove_node_dns(node_id)

    def __dns_state(self):
        if not self.node_id:
            if self.add:
                self.setGlobalDNS(self.dns)
            else:
                self.removeGlobalDNS()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            self.__update_nodes_dns()

            self.__dns_state()

            self.writeState()

        return ReturnMsg(0)
