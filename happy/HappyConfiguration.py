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
#       Implements HappyConfiguration class that modifies user's configuration setup.
#

import os
import sys

from happy.State import State
from happy.ReturnMsg import ReturnMsg
from happy.Utils import *

options = {}
options["quiet"] = False
options["delete"] = None
options["key"] = None
options["value"] = None
options["config-type"] = "user"


def option():
    return options.copy()


class HappyConfiguration(State):
    """
    happy-configuration modifies user's configuration setup.

    happy-configuration [-h --help] [-q --quiet] [-c --config-type (main|log|user)] [-d --delete]
        [-k --key <STRING>] [-v --value <STRING>]

    Example:
    $ happy-configuration weave_path /home/weave/build/x86_64-unknown-linux-gnu/src/test-apps/
        Configures Happy to find weave test clients and servers at the given path

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        State.__init__(self)

        self.quiet = opts["quiet"]
        self.delete = opts["delete"]
        self.key = opts["key"]
        self.value = opts["value"]
        self.config_type = opts["config-type"]
        if not (self.config_type in ('main', 'log', 'user')):
            print "Invalid value for the configuration type"
            print happy.HappyConfiguration.HappyConfiguration.__doc__
            sys.exit(1)

    def __pre_check(self):
        pass

    def __post_check(self):
        pass

    def __print_configuration(self, config_type):
        print config_type.capitalize() + " Happy Configuration"
        if config_type == 'user':
            d = self.configuration
        elif config_type == 'main':
            d = self.main_conf
        elif config_type == 'log':
            d = self.log_conf

        for key in d.keys():
            print "\t" + key + "\t " + str(d[key])
        print

    def run(self):
        self.__pre_check()

        if not self.delete and not self.key:
            self.__print_configuration(self.config_type)
            return ReturnMsg(0)

        if self.config_type == 'user':
            d = self.configuration
        elif self.config_type == 'main':
            d = self.main_conf
        elif self.config_type == 'log':
            d = self.log_conf

        if self.delete:
            if self.delete in d.keys():
                del d[self.delete]

        if self.key is not None and self.value is not None:
            d[self.key] = self.value

        if self.key is not None and self.value is None:
            print "\t" + self.key + "\t",
            if self.key in d.keys():
                print d[self.key]
            else:
                print "not defined"

        self.writeConfiguration(d, self.config_type)

        return ReturnMsg(0)
