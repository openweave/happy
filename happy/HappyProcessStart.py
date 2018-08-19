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
#       Implements HappyProcessStart class that stars process within virtual nodes.
#
#       Process runs a command in a virtual node, which itself
#       is a logical representation of a network namespace.
#

import os
import subprocess
import sys
import time
import psutil

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode
from happy.HappyProcess import HappyProcess
import happy.HappyProcessStop

options = {}
options["quiet"] = False
options["node_id"] = None
options["tag"] = None
options["command"] = None
options["strace"] = False
options["env"] = {}
options["sync_on_output"] = None
options["rootMode"] = False

def option():
    return options.copy()


class HappyProcessStart(HappyNode, HappyProcess):
    """
    Starts a happy process.

    happy-process-start [-h --help] [-q --quiet] [-i --id <NODE_NAME>]
                        [-t --tag <DAEMON_NAME>] [-s --strace]
                        [-e --env <ENVIRONMENT>] <COMMAND>

        -i --id     Optional. Node on which to run the process. Find using
                    happy-node-list or happy-state.
        -t --tag    Required. Name of the process.
        -s --strace Optional. Enable strace output for the process.
        -e --env    Optional. An environment variable to pass to the node
                    for use by the process.
        <COMMAND>   Required. The command to run as process <DAEMON_NAME>.

    Example:
    $ happy-process-start BorderRouter ContinuousPing ping 127.0.0.1
        Starts a process within the BorderRouter node called ContinuousPing
        that runs "ping 127.0.0.1" continuously.

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)
        HappyProcess.__init__(self)

        self.quiet = opts["quiet"]
        self.node_id = opts["node_id"]
        self.tag = opts["tag"]
        self.command = opts["command"]
        self.strace = opts["strace"]
        self.env = opts["env"]
        self.sync_on_output = opts["sync_on_output"]
        self.output_fileput_suffix = ".out"
        self.strace_suffix = ".strace"
        self.rootMode = opts["rootMode"]

    def __stopProcess(self):
        emsg = "Process %s stops itself." % (self.tag)
        self.logger.debug("[%s] daemon [%s]: %s" % (self.node_id, self.tag, emsg))

        options = happy.HappyProcessStop.option()
        options["node_id"] = self.node_id
        options["tag"] = self.tag
        options["quiet"] = self.quiet
        stopProcess = happy.HappyProcessStop.HappyProcessStop(options)
        stopProcess.run()

        self.readState()

    def __pre_check(self):
        # Check if the new process is given
        if not self.tag:
            emsg = "Missing name of the new process to start."
            self.logger.error("[localhost] HappyProcessStart: %s" % (emsg))
            self.exit()

        # Check if the name of new process is not a duplicate (that it does not already exists).
        if self.processExists(self.tag):
            emsg = "virtual process %s already exist." % (self.tag)
            self.logger.info("[%s] HappyProcessStart: %s" % (self.node_id, emsg))
            self.__stopProcess()

        # Check if the process command is given
        if not self.command:
            emsg = "Missing process command."
            self.logger.error("[localhost] HappyProcessStart: %s" % (emsg))
            self.exit()

        timeStamp = "%010.6f" % time.time()
        pid = "%06d" % os.getpid()
        emsg = "Tag: %s PID: %s timeStamp : %s" % (self.tag, pid, timeStamp)
        self.logger.debug("[%s] HappyProcessStart: %s" % (self.node_id, emsg))

        self.output_file = self.process_log_prefix + pid + \
            "_" + timeStamp + "_" + self.tag + self.output_fileput_suffix
        self.strace_file = self.process_log_prefix + pid + \
            "_" + timeStamp + "_" + self.tag + self.strace_suffix

    def __poll_for_output(self):
        poll_interval_sec = 0.01
        max_poll_time_sec = 180
        time_slept = 0
        tail = open(self.output_file, "r")
        self.logger.debug("[%s] HappyProcessStart: polling for output: %s" % (self.node_id, self.sync_on_output))
        while (True):
            line = tail.readline()
            if not line:
                time.sleep(poll_interval_sec)
                time_slept += poll_interval_sec
                poll_interval_sec *= 2
                if (time_slept > max_poll_time_sec):
                    self.logger.debug("[%s] HappyProcessStart: can't find the output requested: %s" %
                                      (self.node_id, self.sync_on_output))
                    raise RuntimeError("Can't find the output requested")

            elif self.sync_on_output in line:
                self.logger.debug("[%s] HappyProcessStart: found output: %s in %s secs" %
                                  (self.node_id, self.sync_on_output, str(time_slept)))
                break
            else:
                continue

        tail.close()
        return

    def __start_daemon(self):
        cmd = self.command

        # We need to support 8 combinations:
        # Who: user or root
        # strace: yes or not
        # env: yes or not

        # Given this script called sayhello.sh:
        #     #!/bin/bash
        #     echo Hello ${USER}!
        #     echo You passed the following opts $1, $2, $3
        #     echo MYENVVAR is $MYENVVAR

        # a successful run with an environment variable prints:
        #     Hello andreello!
        #     You passed the following opts a, b, c
        #     MYENVVAR is hello

        # The goal is to use the simples command line possible; in particular, we don't
        # want to call sudo unless strictly necessary (for performance reasons).

        # Here is how the CLI looks like if you use "ip netns exec" directly:

        # user without env:
        # sudo ip netns exec happy000 sudo -u andreello                                            ./sayhello.sh a b c

        # user with env:
        # sudo ip netns exec happy000 sudo -u andreello                             MYENVVAR=hello ./sayhello.sh a b c

        # root without env:
        #      ip netns exec happy000                                                              ./sayhello.sh a b c

        # root with env
        #      ip netns exec happy000                   bash -c                    'MYENVVAR=hello ./sayhello.sh a b c'

        # user with strace, without env
        # sudo ip netns exec happy000 sudo -u andreello strace -tt -o strace.out                   ./sayhello.sh a b c

        # user with strace, with env
        # sudo ip netns exec happy000 sudo -u andreello strace -tt -o strace.out -E MYENVVAR=hello ./sayhello.sh a b c

        # root with strace, without env
        #      ip netns exec happy000                   strace -tt -o strace.out                   ./sayhello.sh a b c

        # root with strace, with env
        #      ip netns exec happy000                   strace -tt -o strace.out -E MYENVVAR=hello ./sayhello.sh a b c

        # Highlights:
        # - to pass environment variables, either 'strace -E' or 'bash -c'
        # - but, 'bash -c' requires the command to be in one string, while 'strace -E' requires the opposite
        # - the examples above show the argument to 'bash -c' in quotes, but they are not necessary when passing
        #   the list of strings to Popen()
        # - also, the examples above show only one env var; if passing more than one to strace, they need to have
        #   a '-E' each
        # In summary, it's easier to build the cmd as a full string, and then split it the right way depending
        # on strace vs bash.

        # Here are a few examples of how the string is split into a list:
        #
        # user without env:
        # ./bin/happy-process-start.py -i node01 -t HELLO ./sayhello.sh a b c
        # [u'sudo', u'ip', u'netns', u'exec', u'happy000', u'sudo', u'-u', u'andreello', u'./sayhello.sh', u'a', u'b', u'c']
        #
        # user with env:
        # ./bin/happy-process-start.py -i node01 -e "MYENVVAR=hello" -t HELLO ./sayhello.sh a b c
        # [u'sudo', u'ip', u'netns', u'exec', u'happy000', u'sudo', u'-u', u'andreello',
        #       u'MYENVVAR=hello', u'./sayhello.sh', u'a', u'b', u'c']
        #
        # root without env:
        # sudo ./bin/happy-process-start.py -i node01  -t HELLO ./sayhello.sh a b c
        # [u'ip', u'netns', u'exec', u'happy000', u'./sayhello.sh', u'a', u'b', u'c']
        #
        # user with env and strace:
        # ./bin/happy-process-start.py -i node01 -e "MYENVVAR=hello" -s  -t HELLO ./sayhello.sh a b c
        # [u'sudo', u'ip', u'netns', u'exec', u'happy000', u'sudo', u'-u', u'andreello', u'strace', u'-tt', u'-o',
        #       u'/tmp/happy_..._HELLO.strace', u'-E', u'MYENVVAR=hello', u'./sayhello.sh', u'a', u'b', u'c']
        #
        # root with env:
        # [u'ip', u'netns', u'exec', u'happy000', 'bash', '-c', u' MYENVVAR=hello ./sayhello.sh a b c']
        #
        # root with strace no env:
        # sudo ./bin/happy-process-start.py -i node01 -s  -t HELLO ./sayhello.sh a b c
        #
        # root with strace and env:
        # [u'ip', u'netns', u'exec', u'happy000', u'strace', u'-tt', u'-o', u'/tmp/happy_..._HELLO.strace',
        #       u'-E', u'MYENVVAR=hello', u'./sayhello.sh', u'a', u'b', u'c']

        need_internal_sudo = False
        if os.getuid() != 0:
            need_internal_sudo = True

        if "sudo" in cmd.split():
            # The command already has the inner sudo; typical case is that
            # a normal user started Happy, and the script needs to run
            # a command in a node as root. If sudo is for root, remove it.
            # TODO: properly support "sudo -u" with strace
            cmd = self.stripRunAsRoot(cmd)
            need_internal_sudo = False

        env_vars = ""
        for key, value in self.env.items():
            env_vars += key + "=" + value + " "

        self.logger.debug("HappyProcessStart with env: > %s" % (env_vars))

        if self.strace:
            strace = "strace -tt -o " + self.strace_file + " "
            for var in env_vars.split():
                strace += ("-E " + var + " ")
            cmd = strace + cmd
        elif need_internal_sudo:
            cmd = env_vars + cmd
        elif len(env_vars):
            cmd = "bash -c " + env_vars + cmd

        if need_internal_sudo:
            if self.rootMode:
                cmd = self.runAsRoot(cmd)
            else:
                cmd = self.runAsUser(cmd)

        if self.node_id:
            cmd = "ip netns exec " + self.uniquePrefix(self.node_id) + " " + cmd

        cmd = self.runAsRoot(cmd)

        try:
            self.fout = open(self.output_file, "w", 0)
        except Exception:
            emsg = "Failed to open file %s." % (self.output_file)
            self.logger.error("[%s] HappyProcessStart: %s." % (self.node_id, emsg))
            self.exit()

        self.logger.debug("HappyProcessStart: > %s" % (cmd))

        popen = None

        try:

            cmd_list = []
            if "bash -c" in cmd:
                tmp = cmd.split("bash -c")
                cmd_list = tmp[0].split()
                cmd_list = cmd_list + ['bash', '-c'] + [tmp[1]]
            else:
                cmd_list = cmd.split()

            popen = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=self.fout)
            self.child_pid = popen.pid
            emsg = "running daemon %s (PID %d)" % (self.tag, self.child_pid)
            self.logger.debug("[%s] HappyProcessStart: %s" % (self.node_id, emsg))

            # The following is guaranteed to fetch info about the right process (i.e. the PID has
            # no chance of being reused) because even if the child process terminates right away, it'll stay
            # around in <defunct> until the popen object has been destroyed or popen.poll() has
            # been called.
            p = psutil.Process(self.child_pid)
            self.create_time = p.create_time
            emsg = "Create time: " + str(self.create_time)
            self.logger.debug("[%s] HappyProcessStart: %s." % (self.node_id, emsg))

            if self.sync_on_output:
                self.__poll_for_output()

        except Exception as e:
            if popen:
                # We need to kill the process tree; if popen succeeded,
                # we assume we were also able to get the create_time
                self.TerminateProcessTree(popen.pid, self.create_time)

            emsg = "Starting process with command %s FAILED with %s." % (cmd, str(e))
            self.logger.error("[%s] HappyProcessStart: %s." % (self.node_id, emsg))
            self.exit()

    def __post_check(self):
        pass

    def __update_state(self):
        emsg = "Update State with tag %s running command: %s" % \
            (self.tag, self.command)
        self.logger.debug("[%s] HappyProcessStart: %s ." % (self.node_id, emsg))

        new_process = {}
        new_process["pid"] = self.child_pid
        new_process["out"] = self.output_file
        new_process["strace"] = self.strace_file
        new_process["command"] = self.command
        new_process["create_time"] = self.create_time

        self.setNodeProcess(new_process, self.tag, self.node_id)

        self.writeState()

    def run(self):
        with self.getStateLockManager():

            self.readState()

            self.__pre_check()

            self.__start_daemon()

            self.__update_state()

            self.__post_check()

        return ReturnMsg(0)
