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
#       Implements HappyNodeList class that shows virtual nodes.
#

from __future__ import absolute_import
from __future__ import print_function
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyNode import HappyNode

options = {}
options["quiet"] = True


def option():
    return options.copy()


class HappyNodeList(HappyNode):
    """
    Displays a list of virtual nodes.

    happy-node-list [-h --help] [-q --quiet]

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyNode.__init__(self)

        self.quiet = opts["quiet"]

    def __pre_check(self):
        pass

    def __list_nodes(self):
        self.nodes = self.getNodeIds()
        self.nodes.sort()

        for n in self.nodes:
            if not self.quiet:
                self.logger.info(n)

    def __post_check(self):
        pass

    def run(self):
        self.__pre_check()

        self.__list_nodes()

        self.__post_check()

        return ReturnMsg(0, self.nodes)
