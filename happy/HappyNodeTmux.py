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
#       Implements HappyNodeTmux class that manages virtual nodes tmux sessions.
#

import os
import sys
import time

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = False
options["node_id"] = None
options["run_as_user"] = None
options["session"] = None
options["delete"] = False
options["attach"] = True


def option():
    return options.copy()


class HappyNodeTmux(HappyNode):
    """
    happy-node-tmux [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
             [-u --user <USER_NAME>] [-s --session <SESSION_NAME>]
             [-d --delete] [-a --attach] [-n --noattach]
    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.run_as_user = opts["run_as_user"]
        self.session = opts["session"]
        self.delete = opts["delete"]
        self.attach = opts["attach"]
        self.result = None

    def __pre_check(self):
        # Check if the name of the new node is given
        if not self.node_id:
            emsg = "Missing name of the virtual node that should run tmux."
            self.logger.error("[localhost] HappyNodeTmux: %s" % (emsg))
            self.exit()

        # Check if virtual node exists
        if not self._nodeExists():
            emsg = "virtual node does not %s exist." % (self.node_id)
            self.logger.error("[localhost] HappyNodeTmux: %s" % (emsg))
            self.exit()

        # Check if tmux is installed
        cmd = "tmux -V"
        try:
            tmux_version, _ = self.CallAtHostForOutput(cmd)
        except Exception:
            tmux_version = None

        if tmux_version is not None:
            emsg = "Found tmux version %s." % (tmux_version)
            self.logger.debug("[localhost] HappyNodeTmux: %s" % (emsg))
        else:
            emsg = "tmux is not installed."
            self.logger.error("[localhost] HappyNodeTmux: %s" % (emsg))
            emsg = "On Ubuntu, try:   apt-get install tmux ."
            self.logger.error("[localhost] HappyNodeTmux: %s" % (emsg))
            self.exit()

        # Check if user was not passed, thus pick default
        if not self.run_as_user:
            try:
                self.run_as_user = os.environ['USER']

            except Exception:
                emsg = "Failed to retrieve OS environment $USER variable."

                self.logger.error("[%s] HappyNodeTmux: %s" % (self.node_id, emsg))
                self.exit()

        # Check if session name was provided
        if not self.session:
            # By default, pick node_id as a session name
            self.session = self.node_id

    def __has_tmux_server(self):
        return self.session in self.getNodeTmuxSessionIds()

    def __join_tmux_server(self):
        if self.session not in self.getHostTmuxSessionIds():
            emsg = "Cannot find tmux session %s for node %s." % (self.session, self.node_id)
            self.logger.error("[%s] HappyNodeTmux: %s" % (self.node_id, emsg))
            self.exit()

        cmd = "tmux -L "
        cmd += self.node_id
        cmd += " a -t "
        cmd += self.session
        ret = self.CallAtHost(cmd)

    def __add_tmux_state(self):
        new_tmux = {}
        new_tmux["user"] = self.run_as_user
        self.setNodeTmux(self.node_id, self.session, new_tmux)
        self.writeState()

    def __start_tmux_server(self):
        cmd = ""
        cmd = self.runAsUser(cmd, self.run_as_user)
        cmd += ' tmux -L ' + self.node_id + ' new -s ' + self.session + ' -d'

        self.result = self.CallAtNode(self.node_id, cmd)

    def __delete_tmux_state(self):
        self.readState()
        if self.__has_tmux_server():
            self.removeNodeTmux(self.node_id, self.session)
            self.writeState()

    def __delete_tmux_session(self):
        while self.session in self.getHostTmuxSessionIds():
            cmd = "tmux -L "
            cmd += self.node_id
            cmd += " kill-session -t "
            cmd += self.session
            ret = self.CallAtHost(cmd)
            time.sleep(0.1)

    def __post_check(self):
        if self.session not in self.getHostTmuxSessionIds():
            self.__delete_tmux_state()

    def run(self):
        with self.getStateLockManager():

            self.__pre_check()

            if self.delete:
                self.__delete_tmux_session()
                self.__delete_tmux_state()

            else:
                if not self.__has_tmux_server():
                    # start tmux server and attach
                    self.__start_tmux_server()
                    self.__add_tmux_state()
                    time.sleep(0.1)

                if self.attach:
                    # attach to tmux server
                    self.__join_tmux_server()

            self.__post_check()

        return ReturnMsg(0)
