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
#       A Happy command line utility that sends ping among virtual nodes.
#
#       The command is executed by instantiating and running Ping class.
#

import getopt
import sys

import happy.Ping
from happy.Utils import *

if __name__ == "__main__":
    options = happy.Ping.option()
    options["quiet"] = "UNDEFINED"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:qd:s:c:",
                                   ["help", "id=", "quiet", "destination=", "size=", "count="])

    except getopt.GetoptError as err:
        print happy.Ping.Ping.__doc__
        print hred(str(err))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print happy.Ping.Ping.__doc__
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-i", "--id"):
            options["source"] = a

        elif o in ("-d", "--destination"):
            options["destination"] = a

        elif o in ("-a", "--size"):
            options["size"] = a

        elif o in ("-c", "--count"):
            options["count"] = a

        else:
            assert False, "unhandled option"

    if len(args) == 2:
        options["source"] = args[0]
        options["destination"] = args[1]

    if options["quiet"] == "UNDEFINED":
        options["quiet"] = False

    cmd = happy.Ping.Ping(options)
    cmd.start()
