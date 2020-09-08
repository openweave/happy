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
#       Implements HappyTopologyMgr class that provides API to create happy topology
#
#

from __future__ import absolute_import
import happy.HappyNodeDelete

import happy.HappyConfiguration
import happy.HappyDNS
import happy.HappyInternet
import happy.HappyLinkAdd
import happy.HappyLinkDelete
import happy.HappyLinkList
import happy.HappyNetworkAdd
import happy.HappyNetworkAddress
import happy.HappyNetworkDelete
import happy.HappyNetworkList
import happy.HappyNetworkRoute
import happy.HappyNetworkState
import happy.HappyNetworkStatus
import happy.HappyNodeAdd
import happy.HappyNodeAddress
import happy.HappyNodeJoin
import happy.HappyNodeLeave
import happy.HappyNodeList
import happy.HappyNodeRoute
import happy.HappyNodeStatus
import happy.HappyNodeTmux
import happy.Ping
import happy.HappyProcessOutput
import happy.HappyProcessStart
import happy.HappyProcessStop
import happy.HappyProcessStrace
import happy.HappyProcessWait
import happy.HappyState
import happy.HappyStateDelete
import happy.HappyStateLoad
import happy.HappyStateUnload
import happy.Traceroute
import happy.HappyNodeTcpReset


class HappyTopologyMgr(object):
    def HappyConfiguration(self, key=None, value=None, delete=None, quiet=False):
        options = happy.HappyConfiguration.option()
        options["quiet"] = quiet
        options["delete"] = delete
        options["key"] = key
        options["value"] = value

        cmd = happy.HappyConfiguration.HappyConfiguration(options)
        cmd.start()

    def HappyDNS(self, dns=None, node_id=None, add=False, delete=False, quiet=False):
        options = happy.HappyDNS.option()

        options["quiet"] = quiet
        options["add"] = add
        options["delete"] = delete
        options["dns"] = dns
        options["node_id"] = node_id

        cmd = happy.HappyDNS.HappyDNS(options)
        cmd.start()

    def HappyInternet(self, node_id=None, iface=None, add=False, delete=False, quiet=False, isp=None, seed=None):
        options = happy.HappyInternet.option()

        options["quiet"] = quiet
        options["node_id"] = node_id
        options["iface"] = iface
        options["add"] = add
        options["isp"] = isp
        options["seed"] = seed
        options["delete"] = delete

        cmd = happy.HappyInternet.HappyInternet(options)
        cmd.start()

    def HappyLinkAdd(self, type=None, tap=False, quiet=False):
        options = happy.HappyLinkAdd.option()
        options["quiet"] = quiet
        options["type"] = type
        options["tap"] = tap

        cmd = happy.HappyLinkAdd.HappyLinkAdd(options)
        cmd.start()

    def HappyLinkDelete(self, link_id=None, quiet=False):
        options = happy.HappyLinkDelete.option()
        options["quiet"] = quiet
        options["link_id"] = link_id

        cmd = happy.HappyLinkDelete.HappyLinkDelete(options)
        cmd.start()

    def HappyLinkList(self, quiet=False):
        options = happy.HappyLinkList.option()
        options["quiet"] = quiet
        cmd = happy.HappyLinkList.HappyLinkList(options)
        cmd.start()

    def HappyNetworkAdd(self, network_id=None, type=None, quiet=False):
        options = happy.HappyNetworkAdd.option()
        options["quiet"] = quiet
        options["network_id"] = network_id
        options["type"] = type

        cmd = happy.HappyNetworkAdd.HappyNetworkAdd(options)
        cmd.start()

    def HappyNetworkAddress(self, network_id=None, address=None, add=False, delete=False, quiet=False):
        options = happy.HappyNetworkAddress.option()

        options["quiet"] = quiet
        options["network_id"] = network_id
        options["add"] = add
        options["delete"] = delete
        options["address"] = address

        cmd = happy.HappyNetworkAddress.HappyNetworkAddress(options)
        cmd.start()

    def HappyNetworkDelete(self, network_id=None, quiet=False):
        options = happy.HappyNetworkDelete.option()
        options["quiet"] = quiet
        options["network_id"] = network_id
        cmd = happy.HappyNetworkDelete.HappyNetworkDelete(options)
        cmd.start()

    def HappyNetworkList(self, quiet=False):
        options = happy.HappyNetworkList.option()
        options["quiet"] = quiet
        cmd = happy.HappyNetworkList.HappyNetworkList(options)
        cmd.start()

    def HappyNetworkRoute(self, network_id=None, add=False, delete=False, to=None, via=None,
                          prefix=None, record=None, quiet=False, isp=None, seed=None):
        options = happy.HappyNetworkRoute.option()

        options["quiet"] = quiet
        options["network_id"] = network_id
        options["add"] = add
        options["delete"] = delete
        options["to"] = to
        options["via"] = via
        options["prefix"] = prefix
        options["record"] = record
        options["isp"] = isp
        options["seed"] = seed
        cmd = happy.HappyNetworkRoute.HappyNetworkRoute(options)
        cmd.start()

    def HappyNetworkState(self, network_id=None, up=False, down=False, quiet=False):
        options = happy.HappyNetworkState.option()
        options["quiet"] = quiet
        options["network_id"] = network_id
        options["up"] = up
        options["down"] = down
        cmd = happy.HappyNetworkState.HappyNetworkState(options)
        cmd.start()

    def HappyNetworkStatus(self, network_id=None, quiet=False):
        options = happy.HappyNetworkStatus.option()
        options["quiet"] = quiet
        options["network_id"] = network_id
        cmd = happy.HappyNetworkStatus.HappyNetworkStatus(options)
        cmd.start()

    def HappyNodeAdd(self, node_id=None, type=None, quiet=False):
        options = happy.HappyNodeAdd.option()
        options["node_id"] = node_id
        options["quiet"] = quiet
        options["type"] = type

        cmd = happy.HappyNodeAdd.HappyNodeAdd(options)
        cmd.start()

    def HappyNodeAddress(self, node_id=None, interface=None, add=False, delete=False, address=None, quiet=False):
        options = happy.HappyNodeAddress.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["interface"] = interface
        options["add"] = add
        options["delete"] = delete
        options["address"] = address
        cmd = happy.HappyNodeAddress.HappyNodeAddress(options)
        cmd.start()

    def HappyNodeDelete(self, node_id=None, quiet=False):
        options = happy.HappyNodeDelete.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        cmd = happy.HappyNodeDelete.HappyNodeDelete(options)
        cmd.start()

    def HappyNodeJoin(self, node_id=None, tap=False, network_id=None, fix_hw_addr=None, customized_eui64=None,
                      quiet=False):
        options = happy.HappyNodeJoin.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tap"] = tap
        options["network_id"] = network_id
        options["fix_hw_addr"] = fix_hw_addr
        options["customized_eui64"] = customized_eui64
        cmd = happy.HappyNodeJoin.HappyNodeJoin(options)
        cmd.start()

    def HappyNodeLeave(self, node_id=None, network_id=None, quiet=False):
        options = happy.HappyNodeLeave.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["network_id"] = network_id
        cmd = happy.HappyNodeLeave.HappyNodeLeave(options)
        cmd.start()

    def HappyNodeList(self, quiet=False):
        options = happy.HappyNodeList.option()
        options["quiet"] = quiet
        cmd = happy.HappyNodeList.HappyNodeList(options)
        cmd.start()

    def HappyNodeRoute(self, node_id=None, add=False, delete=False, to=None, via=None, prefix=None,
                       record=True, quiet=False, isp=None, seed=None):
        options = happy.HappyNodeRoute.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["add"] = add
        options["delete"] = delete
        options["to"] = to
        options["via"] = via
        options["prefix"] = prefix
        options["record"] = record
        options["isp"] = isp
        options["seed"] = seed
        cmd = happy.HappyNodeRoute.HappyNodeRoute(options)
        cmd.start()

    def HappyNodeStatus(self, node_id=None, quiet=False):
        options = happy.HappyNodeStatus.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        cmd = happy.HappyNodeStatus.HappyNodeStatus(options)
        cmd.start()

    def HappyNodeTmux(self, node_id=None, run_as_user=None, session=None, delete=False, attach=True, quiet=False):
        options = happy.HappyNodeTmux.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["run_as_user"] = run_as_user
        options["session"] = session
        options["delete"] = delete
        options["attach"] = attach
        cmd = happy.HappyNodeTmux.HappyNodeTmux(options)
        cmd.start()

    def HappyPing(self, source=None, destination=None, size=None, count=None, quiet=False):
        options = happy.Ping.option()
        options["quiet"] = quiet
        options["source"] = source
        options["destination"] = destination
        options["size"] = size
        options["count"] = count

        cmd = happy.Ping.Ping(options)
        cmd.start()

    def HappyProcessOutput(self, node_id=None, tag=None, quiet=False):
        options = happy.HappyProcessOutput.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tag"] = tag
        cmd = happy.HappyProcessOutput.HappyProcessOutput(options)
        cmd.start()

    def HappyProcessStart(self, node_id=None, tag=None, command=None, strace=False, quiet=False):
        options = happy.HappyProcessStart.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tag"] = tag
        options["command"] = command
        options["strace"] = strace
        cmd = happy.HappyProcessStart.HappyProcessStart(options)
        cmd.start()

    def HappyProcessStop(self, node_id=None, tag=None, quiet=False):
        options = happy.HappyProcessStop.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tag"] = tag
        cmd = happy.HappyProcessStop.HappyProcessStop(options)
        cmd.start()

    def HappyProcessStrace(self, node_id=None, tag=None, quiet=False):
        options = happy.HappyProcessStrace.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tag"] = tag
        cmd = happy.HappyProcessStrace.HappyProcessStrace(options)
        cmd.start()

    def HappyProcessWait(self, node_id=None, tag=None, timeout=None, quiet=False):
        options = happy.HappyProcessWait.option()
        options["quiet"] = quiet
        options["node_id"] = node_id
        options["tag"] = tag
        options["timeout"] = timeout
        cmd = happy.HappyProcessWait.HappyProcessWait(options)
        cmd.start()

    def HappyState(self, save=None, graph=None, log=False, json=False, unlock=False, id=False, all=False, quiet=False):
        options = happy.HappyState.option()
        options["quiet"] = quiet
        options["save"] = save
        options["graph"] = graph
        options["log"] = log
        options["json"] = json
        options["unlock"] = unlock
        options["id"] = id
        options["all"] = all
        cmd = happy.HappyState.HappyState(options)
        cmd.start()

    def HappyStateDelete(self, force=False, all=False, quiet=False):
        options = happy.HappyStateDelete.option()
        options["quiet"] = quiet
        options["force"] = force
        options["all"] = all

        cmd = happy.HappyStateDelete.HappyStateDelete(options)
        cmd.start()

    def HappyStateLoad(self, json_file=None, quiet=False):
        options = happy.HappyStateLoad.option()
        options["quiet"] = quiet
        options["json_file"] = json_file
        cmd = happy.HappyStateLoad.HappyStateLoad(options)
        cmd.start()

    def HappyStateUnload(self, json_file=None, quiet=False):
        options = happy.HappyStateUnload.option()
        options["quiet"] = quiet
        options["json_file"] = json_file
        cmd = happy.HappyStateUnload.HappyStateUnload(options)
        cmd.start()

    def HappyTraceroute(self, source=None, destination=None, quiet=False):
        options = happy.Traceroute.option()
        options["quiet"] = quiet
        options["source"] = source
        options["destination"] = destination
        cmd = happy.Traceroute.Traceroute(options)
        cmd.start()

    def HappyNodeTcpReset(self, node_id=None, quiet=False, action=None, interface="wlan0", ips=None,
                          dstPort=None, start=0, duration=10):
        options = happy.HappyNodeTcpReset.option()
        options["node_id"] = node_id
        options['interface'] = interface
        options['quiet'] = quiet
        options['action'] = action
        options['ips'] = ips
        options['dstPort'] = dstPort
        options['start'] = start
        options['duration'] = duration
        cmd = happy.HappyNodeTcpReset.HappyNodeTcpReset(options)
        cmd.start()
