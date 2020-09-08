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
#       Implements Driver class, the set of main tools and mechanisms
#       necessary to run Happy. Most other classes inherit Driver.
#

from __future__ import absolute_import
from __future__ import print_function
import getopt
import getpass
import json
import lockfile
import logging
import logging.config
import logging.handlers
import os
import subprocess
import sys
import time
import warnings

import happy.HappyLogger as HappyLogger
from happy.utils.IP import IP
from happy.Utils import *

log_config = "conf/log_config.json"
main_config = "conf/main_config.json"


class HappyException(Exception):
    pass

g_locks = {"state": None, "rt": None, "isp": None}


class StateLock(object):
    """ A wrapper for lockfile.FileLock that is re-entrant.
    """
    def __init__(self, name, maxattempts, filename, logger):
        self.name = name
        self.filename = filename
        self.maxattempts = maxattempts
        self.filelock = lockfile.FileLock(self.filename)
        self.counter = 0
        self.logger = logger
        warnings.filterwarnings("ignore", category=ResourceWarning)

    def lock(self):
        wait_time = 0.1
        wait_attempts = 0

        while True:
            try:
                if self.filelock.i_am_locking():
                    self.counter += 1
                    break
                self.filelock.acquire(timeout=wait_time)
                break
            except lockfile.LockTimeout:
                pass
            wait_attempts += 1
            if wait_attempts % self.maxattempts == 0:
                emsg = "Waiting for %s for over %d seconds. Break and Kill itself." % (self.name, wait_time * wait_attempts)
                self.logger.error("[localhost] Happy: %s" % (emsg))
                raise HappyException(emsg)

            if wait_attempts % 10 == 0:
                emsg = "Waiting for %s for over %.2f seconds." % (self.name, wait_time * wait_attempts)
                self.logger.warning("[localhost] Happy: %s" % (emsg))

    def release(self):
        try:
            if self.counter > 0:
                self.counter -= 1
            else:
                self.filelock.release()
        except Exception:
            self.filelock.break_lock()
            self.counter = 0
            emsg = "Unlocking %s state failed." % self.name
            self.logger.warning("[localhost] Happy: %s" % (emsg))

    def break_lock(self):
        if self.filelock.is_locked():
            self.filelock.break_lock()


class StateLockManager(object):
    """
    A context manager that wraps a StateLock.
    """
    def __init__(self, lock):
        self.state_lock = lock
        return None

    def __enter__(self):
        self.state_lock.lock()
        return self

    def __exit__(self, *args):
        self.state_lock.release()
        return None

    def break_lock(self):
        self.state_lock.break_lock()


class Driver:
    """
    Driver init loads configuration base on conf/log_config.json and conf/main_config.json
    """
    def __init__(self):
        self.state = {}
        self.isp_state = {}
        self.configuration = {}
        self.log_conf = None
        self.logger = None

        self.happy_path = os.path.dirname(os.path.realpath("%s" % (__file__)))

        self.log_conf_file = self.happy_path + "/" + log_config
        self.main_conf_file = self.happy_path + "/" + main_config

        self.__configure()
        self.readConfiguration()
        self.configHappyLogPath()
        self.__logging()

        if not g_locks["state"]:
            g_locks["state"] = StateLock("state", 100, self.state_file, self.logger)
        if not g_locks["rt"]:
            g_locks["rt"] = StateLock("rt", 5000, self.rt_state_file, self.logger)

        self.readState()

    def init_happy_isp(self, isp_id):
        self.isp_state_file = os.path.expanduser(self.state_file_prefix + isp_id + self.isp_suffix + self.state_file_suffix)
        if not g_locks["isp"]:
            g_locks["isp"] = StateLock("isp", 5000, self.isp_state_file, self.logger)

    def getLogConfigPath(self):
        return self.log_conf_file

    def getLogConfig(self):
        return self.log_conf

    def getMainConfigPath(self):
        return self.main_conf_file

    def getMainConfig(self):
        return self.main_conf

    def __configure(self):
        try:
            with open(self.main_conf_file, 'r') as jfile:
                json_data = jfile.read()

            self.main_conf = json.loads(json_data)
        except Exception:
            print("Failed to load config from %s." % (self.main_conf_file))
            sys.exit(1)

        try:
            self.default_state = self.main_conf["default_state"]
        except Exception:
            print("Failed to find default state name in the main configuration file %s." \
                % (self.main_conf_file))
            sys.exit(1)

        try:
            self.state_environ = self.main_conf["state_environ"]
        except Exception:
            print("Failed to find state environment variable name in the main configuration file %s." \
                % (self.main_conf_file))
            sys.exit(1)

        try:
            self.state_id = self.getStateId()
        except Exception:
            print("Failed to get state id from %s." % (self.main_conf_file))
            sys.exit(1)

        # default_happy_log_dir will be default dir for happy log
        # happy_log_environ is os environment variable passed from test-engine
        try:
            self.default_happy_log_dir = self.main_conf["default_happy_log_dir"]
        except Exception:
            print("Failed to find default_happy_log dir in the main configuration file %s." \
                % (self.main_conf_file))
            sys.exit(1)

        try:
            self.happy_log_environ = "HAPPY_LOG_DIR"
        except Exception:
            print("Failed to find happy log environment variable name in the main configuration file %s." \
                % (self.main_conf_file))
            sys.exit(1)

        try:
            self.happy_log_dir = self.getHappyLogDir()
        except Exception:
            print("Failed to get happy log dir from %s." % (self.main_conf_file))
            sys.exit(1)

        try:
            self.state_file_prefix = self.main_conf["state_file_prefix"]
            self.state_file_suffix = self.main_conf["state_file_suffix"]
            self.isp_suffix = self.main_conf["default_isp_suffix"]
            self.rt_suffix = self.main_conf["default_rt_suffix"]
            self.state_file = os.path.expanduser(
                self.state_file_prefix + self.state_id + self.state_file_suffix)
            self.rt_state_file = os.path.expanduser(self.state_file_prefix + self.rt_suffix + self.state_file_suffix)
            self.configuration_file = os.path.expanduser(self.main_conf["configuration_file"])

        except Exception:
            print("Failed to parse main configuration for state file names: %s" \
                % (self.main_conf_file))
            sys.exit(1)

        try:
            self.log_level_file = os.environ["HAPPY_LOG_LEVEL_FILE"]
        except:
            self.log_level_file = self.main_conf.get("log_level_file", "DEBUG")

        try:
            self.log_level_console = os.environ["HAPPY_LOG_LEVEL_CONSOLE"]
        except:
            self.log_level_console = self.main_conf.get("log_level_console", "INFO")

    def __logging(self):
        try:
            with open(self.log_conf_file, 'r') as jfile:
                json_data = jfile.read()

                self.log_conf = json.loads(json_data)
        except Exception:
            print("Failed to load config from %s." % (self.log_conf_file))
            sys.exit(1)

        try:
            confDict = dict(self.main_conf)
            confDict['state_id'] = self.state_id
            confDict['happy_log_dir'] = self.happy_log_dir

            self.log_conf['handlers']['file']['filename'] = self.log_conf['handlers']['file']['filename'] % confDict
            self.log_conf['handlers']['file']['level'] = logging.getLevelName(self.log_level_file)
            self.log_conf['handlers']['stream']['level'] = logging.getLevelName(self.log_level_console)

            logging.config.dictConfig(self.log_conf)
            self.logger = logging.getLogger(__name__)

            h = HappyLogger.HostnameFilter()

        except ValueError as e:
            emsg = "Failed to load logging configuration: "
            print(emsg)
            print(e)
            sys.exit(1)

        except TypeError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

        except AttributeError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

        except ImportError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

    def __initConfiguration(self):
        self.configuration = {}

    def readConfiguration(self):
        try:
            with open(self.configuration_file, 'r') as jfile:
                json_data = jfile.read()

            self.configuration = json.loads(json_data)

            if not bool(self.configuration):
                self.__initConfiguration()

        except Exception:
            self.__initConfiguration()

    def configHappyLogPath(self):
        """
        set happy test log path if happy_log_path in ~/.happy_conf.json
        log_directory=happy_log_path if happy_log_path in ~/.happy_conf.json
        """
        try:
            if "happy_log_path" in self.configuration:
                self.main_conf["log_directory"] = self.configuration["happy_log_path"]

            confDict = dict(self.main_conf)
            confDict['state_id'] = self.state_id
            confDict['happy_log_dir'] = self.happy_log_dir

            if not os.path.exists(self.happy_log_dir):
                os.makedirs(self.happy_log_dir)

            self.process_log_prefix = self.main_conf["process_log_prefix"] % confDict

        except Exception as e:
            print("Failed to find process's log prefix in the main configuration file %s. Exception %s" \
                % (self.main_conf_file, str(e)))
            sys.exit(1)

    def writeConfiguration(self, configuration, config_type='user'):
        try:
            json_data = json.dumps(configuration, sort_keys=True, indent=4)
        except Exception:
            msg = "Failed to save configuration file: %s" % \
                (self.configuration_file)
            self.logger.error(msg)
            self.exit()

        if config_type == 'user':
            filename = self.configuration_file
        elif config_type == 'main':
            filename = self.getMainConfigPath()
        elif config_type == 'log':
            filename = self.getLogConfigPath()
        else:
            emsg = "Invalid configuration type: %s" % (str(config_type))
            print(emsg)
            sys.exit(1)

        with open(filename, 'w') as jfile:
            jfile.write(json_data)
            jfile.flush()
            os.fsync(jfile)

        self.readConfiguration()
        return 0

    def getStateLockManager(self, lock_id="state"):
        """
        Returns a context manager that wraps the StateLock specified by
        lock_id.
        """
        return StateLockManager(g_locks[lock_id])

    def lockState(self, lock_id="state"):
        return g_lock[lock_id].lock()

    def unlockState(self, lock_id="state"):
        return g_lock[lock_id].release()

    def exit(self):
        sys.exit(1)

    def RaiseError(self, msg=None):
        raise HappyException(msg)

    def readState(self):
        modified_time = None
        try:
            with open(self.state_file, 'r') as jfile:
                modified_time = os.path.getmtime(self.state_file)
                json_data = jfile.read()

            self.state = json.loads(json_data)

        except Exception:
            pass

    def readIspState(self):
        modified_isp_time = None
        try:
            with open(self.isp_state_file, 'r') as jfile:
                modified_isp_time = os.path.getmtime(self.isp_state_file)
                json_isp_data = jfile.read()
            self.isp_state = json.loads(json_isp_data)

        except Exception:
            pass

    def writeState(self, state=None):
        self.logger.debug("Happy: writing Happy state to file")
        if state is None:
            state = self.state

        try:
            json_data = json.dumps(state, sort_keys=True, indent=4)
        except Exception:
            msg = "Failed to save state file: %s" % \
                (self.state_file)
            self.logger.error(msg)
            self.exit()

        with open(self.state_file, 'w') as jfile:
            jfile.write(json_data)
            jfile.flush()
            os.fsync(jfile)

        self.readState()
        return 0

    def writeIspState(self, state=None):
        if state is None:
            state = self.isp_state

        try:
            json_isp_data = json.dumps(state, sort_keys=True, indent=4)
        except Exception:
            msg = "Failed to save state file: %s" % \
                (self.isp_state_file)
            self.logger.error(msg)
            self.exit()

        with open(self.isp_state_file, 'w') as jfile:
            jfile.write(json_isp_data)
            jfile.flush()
            os.fsync(jfile)

        self.readIspState()
        return 0

    def start(self):
        x = self.run()
        return x

    def CallCmd(self, cmd, env=None, quiet=False, output='debuglog'):
        localEnv = dict(os.environ)

        if env is not None:
            localEnv.update(env)
        cmd = cmd.encode("ascii")

        self.logger.debug("Happy [%s]: > %s" % (self.state_id, cmd))

        if output == 'debuglog':
            fd = subprocess.PIPE
        elif output == 'shell':
            fd = None
        try:
            process = subprocess.Popen(cmd.split(),
                                       stdout=fd,
                                       stderr=fd,
                                       env=localEnv)
        except subprocess.CalledProcessError as e:
            self.logger.warning("[localhost] Happy: %s" % e)
            emsg = "subprocess.Popen '%s' might failed" % cmd
            self.logger.warning(emsg)
            return None, None, None

        except Exception:
            emsg = "System call: '%s' FAILED" % cmd
            self.logger.warning(emsg)
            return None, None, None

        result = process.wait()

        if output == 'shell':
            return result, None, None
        else:
            out_result = process.stdout.read().decode("utf-8")
            err_result = process.stderr.read().decode("utf-8")
            if out_result is not None:
                for line in out_result.split("\n"):
                    if len(line) > 0:
                        self.logger.debug("Happy [%s]:      %s" % (self.state_id, line))

            if err_result is not None:
                for line in err_result.split("\n"):
                    if len(line) > 0:
                        self.logger.debug("Happy [%s]:      %s" % (self.state_id, line))

            return result, out_result, err_result

    def CallAtHost(self, cmd, env=None, quiet=False, output='debuglog'):
        result, out_result, err_result = self.CallCmd(cmd, env, quiet, output)
        return result

    def CallAtHostForOutput(self, cmd, env=None, quiet=False):
        result, out_result, err_result = self.CallCmd(cmd, env, quiet)
        return out_result, err_result

    def isNodeLocal(self, node_id=None):
        if node_id is None:
            try:
                node_id = self.node_id
            except Exception:
                return False

        node_type = self.getNodeType(node_id)

        if node_type is not None and node_type == "local":
            return True
        else:
            return False

    def stripRunAsRoot(self, cmd):
        sudoPrefix = self.runAsRoot('')
        if cmd.startswith(sudoPrefix) and not cmd.startswith(sudoPrefix + '-u'):
            return cmd[len(sudoPrefix):]

        return cmd

    def CallAtNode(self, node_id, cmd, env=None, quiet=False, output='debuglog'):
        if self.isNodeLocal(node_id):
            return self.CallAtHost(cmd, env=env, quiet=quiet, output=output)

        cmd = self.runAsRoot("ip netns exec %s %s" % (self.uniquePrefix(node_id), self.stripRunAsRoot(cmd)))
        return self.CallAtHost(cmd, env=env, quiet=quiet, output=output)

    def CallAtNetwork(self, network_id, cmd, env=None, quiet=False):
        return self.CallAtNode(network_id, cmd, env=env, quiet=quiet)

    def CallAtNodeForOutput(self, node_id, cmd, env=None):
        if self.isNodeLocal(node_id):
            return self.CallAtHostForOutput(cmd, env=env)

        cmd = "ip netns exec %s %s" % (self.uniquePrefix(node_id), self.stripRunAsRoot(cmd))
        cmd = self.runAsRoot(cmd)

        return self.CallAtHostForOutput(cmd, env=env)

    def CallAtNetworkForOutput(self, network_id, cmd, env=None):
        return self.CallAtNodeForOutput(network_id, cmd, env)

    def getRunAsRootPrefixList(self):
        if "SUDO" in list(os.environ.keys()):
            return [os.environ["SUDO"]]
        elif os.getuid() == 0:
            # We are already root
            return []
        else:
            return ["sudo"]


    def runAsRoot(self, cmd):
        return ' '.join(self.getRunAsRootPrefixList() + [cmd])

    def getRunAsUserPrefixList(self, username=None):
        if username is None:
            username = getpass.getuser()

        if "SUDO" in list(os.environ.keys()):
            return [os.environ["SUDO"], "-u", username]
        else:
            return ["sudo", "-u", username]

    def runAsUser(self, cmd, username=None):
        return ' '.join(self.getRunAsUserPrefixList(username=username) + [cmd])

    def uniquePrefix(self, txt, state=None):
        prefix = self.getStateId(state)
        return prefix + self.getShortIdentifier(txt, state)

    def getShortIdToLongIdMap(self, state=None):
        state = self.getState(state)
        if "identifiers" not in list(state.keys()):
            state["identifiers"] = {}
        return state["identifiers"]

    def getLongIdToShortIdMap(self, state=None):
        state = self.getState(state)
        if "netns" not in list(state.keys()):
            state["netns"] = {}
        return state["netns"]

    def createShortIdentifier(self, identifier, state=None):
        identifiers = self.getShortIdToLongIdMap(state)

        id_num = len(identifiers)
        newKey = "%03d" % (id_num)

        while newKey in identifiers:
            emsg = "Detected Key collision, attempting to fix"
            self.logger.error("Driver: %s" % emsg)
            id_num = id_num+1
            newKey = "%03d" % (id_num)

        identifiers[newKey] = {'id': identifier}

        return newKey

    def getShortIdentifier(self, identifier, state=None):
        identifiers = self.getShortIdToLongIdMap(state)
        longToShortMap = self.getLongIdToShortIdMap(state)

        if identifier not in longToShortMap:
            key = self.createShortIdentifier(identifier, state)
            longToShortMap[identifier] = key

        return longToShortMap[identifier]

    def getStateId(self, state=None):
        if state is not None and len(list(state.keys())) > 0:
            state_key = list(state.keys())[0]
            return state_key

        if self.state_environ in list(os.environ.keys()):
            return os.environ[self.state_environ]
        else:
            return self.default_state

    def getHappyLogDir(self):
        if self.happy_log_environ in list(os.environ.keys()):
            return os.environ[self.happy_log_environ]
        else:
            return self.default_happy_log_dir
