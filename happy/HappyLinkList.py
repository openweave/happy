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
#       Implements HappyLinkList class that displays a list of virtual links.
#

from __future__ import absolute_import
from __future__ import print_function
import os
import sys

from happy.ReturnMsg import ReturnMsg
from happy.Utils import *
from happy.HappyLink import HappyLink

options = {}
options["quiet"] = False


def option():
    return options.copy()


class HappyLinkList(HappyLink):
    """
    Displays a list of virtual links.

    happy-link-list [-h --help] [-q --quiet]

    return:
        0    success
        1    fail
    """

    def __init__(self, opts=options):
        HappyLink.__init__(self)

        self.quiet = opts["quiet"]

    def __pre_check(self):
        pass

    def __list_links(self):
        cmd = "ip link show"
        result, _ = self.CallAtHostForOutput(cmd)

        if result != "":
            self.logger.info(result)

    def __show_links(self):
        if self.quiet:
            return

        link_ids = self.getLinkIds()
        link_ids.sort()

        for link_id in link_ids:
            print(link_id)

            if self.getLinkNetwork(link_id) is None:
                print("\tNetwork: not assigned")
            else:
                print("\tNetwork: " + self.getLinkNetwork(link_id))

            if self.getLinkNode(link_id) is None:
                print("\tNode: not assigned")
            else:
                print("\tNode: " + self.getLinkNode(link_id))

            print("\tType: " + self.getLinkType(link_id))
            print()

    def __post_check(self):
        pass

    def run(self):
        self.__pre_check()

        self.__show_links()

        self.__post_check()

        return ReturnMsg(0)
