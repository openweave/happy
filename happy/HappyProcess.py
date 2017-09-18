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
#       Implements HappyProcess class that manages happy processes.
#

import os
import psutil
import sys
import time
import math

from happy.Utils import *
from happy.HappyHost import HappyHost
import happy.HappyLinkDelete


class HappyProcess(HappyHost):
    def __init__(self, node_id=None):
        HappyHost.__init__(self)

    def processExists(self, tag, node_id=None):
        if node_id is None:
            node_id = self.node_id

        pid = self.getNodeProcessPID(tag, node_id)
        create_time = self.getNodeProcessCreateTime(tag, node_id)

        if pid is None:
            return False

        try:
            p = psutil.Process(pid)
            return p.is_running() and p.create_time == create_time and p.status not in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]
        except Exception:
            return False

    def BlockOnProcessPID(self, pid, create_time, timeout=None):
        if pid is None:
            return
        p = None
        try:
            p = psutil.Process(pid)
            if p.is_running() and p.create_time == create_time and p.status not in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                val = p.wait(timeout)
                if val is None:
                    self.logger.debug("Process is terminated ")
                else:
                    self.logger.debug("Process is terminated, possibly by os ")
        except psutil.TimeoutExpired:
            self.logger.info("TimeoutExpired happens")
            if p is not None:
                self.logger.info("kill process")
                self.TerminateProcessTree(pid, create_time)
        except Exception:
            self.logger.debug("Process is terminated for unknown reasons")
            pass
        return

    def BlockOnProcess(self, tag, node_id=None, timeout=None):
        if node_id is None:
            node_id = self.node_id

        pid = self.getNodeProcessPID(tag, node_id)
        create_time = self.getNodeProcessCreateTime(tag, node_id)

        if pid is None:
            return

        self.BlockOnProcessPID(pid, create_time, timeout)

    def GetProcessTreeAsList(self, pid, create_time):
        try:
            p = psutil.Process(pid)
            if (p.create_time != create_time):
                return []
            childs = p.get_children(recursive=True)
            # At the time of this writing, get_children returns a list of the
            # children in breadth-first order. All leaves
            # are at the end of the list.
            return [p] + childs
        except Exception:
            return []

    def __wait_procs(self, procs, timeout):
        before = time.time()
        after = before

        alive = procs

        # (old versions of psutil have a bug and return too soon)
        while alive and (after - before) < timeout:
            next_timeout = math.ceil(timeout - (after - before))
            gone, alive = psutil.wait_procs(alive, timeout=next_timeout)
            after = time.time()
            if after < before:
                after = before
        return alive

    def __signal_procs(self, procs, signal):
        for c in procs:
            try:
                # We sudo, in case we don't own the process
                cmd = "kill -" + signal + " " + str(c.pid)
                cmd = self.runAsRoot(cmd)
                ret = self.CallAtHost(cmd)
                if (ret != 0):
                    emsg = "Failed to send %s to process with PID %s." % (signal, str(c.pid))
                    self.logger.debug("[%s] HappyProcessStop: %s" % (self.node_id, emsg))
            except Exception:
                emsg = "Failed to send %s to process with PID %s." % (signal, str(c.pid))
                self.logger.debug("[%s] HappyProcessStop: %s" % (self.node_id, emsg))
                pass

    def TerminateProcessTree(self, pid, create_time):
        # HappyProcessStart creates a tree of processes.
        # For example, if a normal user types "happy-process-start node01 ping ...",
        # ps reports:
        # root     141987  0.1  0.0  88764  5480 pts/43   S    19:37   0:00 sudo ip netns exec happy000 sudo -u andreello ping 127.0.0.1
        # root     141988  0.1  0.1 124400 42524 pts/43   S    19:37   0:00  \_ sudo -u andreello ping 127.0.0.1
        # andreel+ 141989  0.0  0.0   6500   628 pts/43   S    19:37   0:00      \_ ping 127.0.0.1

        # But in some cases it will create only one process.
        # If the command above is entered by root, ps shows:
        #
        # root     142652  0.0  0.0   6500   628 pts/43   S    19:41   0:00 ping 127.0.0.1
        #
        # Note that HappyProcessStart stores the pid of the oldest parent.
        #
        # The goal is to send a SIGUSR1 to the actual process (in the example above, 'watch ls')
        # If the process has not registered a handler for SIGUSR1, it will be terminated.
        # Otherwise, the test process should handle the signal by cleaning up and exiting gracefully.
        # All processes up the hierarchy should then exit naturally.
        #
        # So, it should be sufficient to send a SIGUSR1 to the youngest child process.
        # But, we want to support the case of a process that itself spawns several children.
        # For that reason, the code below sends a SIGUSR1 to all children of the main process
        # and to the main process itself without checking if a process is a leaf of the tree or not.
        # Note that sudo relays the signals it receives to its child process, so we're potentially
        # sending the same signal twice to some of the children.
        #
        # Note that sending signals to different processes is not atomic, and so we don't know
        # in which order the processes will actually exit. Also, PIDs can be reused, and so
        # while looping through the process list and sending signals, there is no hard guarantee
        # that the PID we're sending a signal to is still the same process.
        # We do know that the PID stored in the happy state still refers to the right process because
        # we also store and double check the create_time attribute.
        # psutil also checks timestamps between invocations, and so psutil.wait_procs() won't get
        # fooled by a new process having the same PID as one of the PIDs in procs.
        # If we wanted to send signals using psutil we'd need to be root as most of the
        # Happy processes belong to root.
        #
        # If the processes have not terminated after 30 seconds, they are sent a SIGTERM, and
        # and then a SIGKILL.
        # The timeouts are set at 30 seconds in case many Happy instances are run in parallel
        # and the system is under heavy load.
        #

        procs = self.GetProcessTreeAsList(pid, create_time)

        # first send SIGUSR1
        self.__signal_procs(procs, "SIGUSR1")

        alive = self.__wait_procs(procs, 30)

        if alive:
            # if process ignored SIGUSR1, try sending terminate
            self.__signal_procs(alive, "SIGTERM")

            alive = self.__wait_procs(alive, 30)

        if alive:
            # if process is still around, just kill it
            self.__signal_procs(alive, "SIGKILL")
