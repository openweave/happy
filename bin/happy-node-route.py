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
#       A Happy command line utility that manipulates virtual node IP addresses.
#
#       The command is executed by instantiating and running HappyNodeRoute class.
#

import getopt
import sys

import happy.HappyNodeRoute
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyNodeRoute.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:qadt:v:p:s:e:y:",
                                   ["help", "id=", "quiet", "add", "delete", "to=", "via=", "prefix=", "isp=", "seed=", "type="])

    except getopt.GetoptError as err:
        print happy.HappyNodeRoute.HappyNodeRoute.__doc__
        print hred(str(err))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print happy.HappyNodeRoute.HappyNodeRoute.__doc__
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-i", "--id"):
            options["node_id"] = a

        elif o in ("-t", "--to"):
            options["to"] = a

        elif o in ("-v", "--via"):
            options["via"] = a

        elif o in ("-p", "--prefix"):
            options["prefix"] = a

        elif o in ("-a", "--add"):
            options["add"] = True

        elif o in ("-d", "--delete"):
            options["delete"] = True

        elif o in ("-s", "--isp"):
            options["isp"] = True

        elif o in ("-e", "--seed"):
            options["seed"] = True

        elif o in ("-y", "--type"):
            options["route_type"] = a

        else:
            assert False, "unhandled option"

    if len(args) == 1:
        options["node_id"] = args[0]

    if len(args) == 2:
        options["node_id"] = args[0]
        options["to"] = "default"
        options["via"] = args[1]

    if len(args) == 3:
        options["node_id"] = args[0]
        options["to"] = args[1]
        options["via"] = args[2]

    if len(args) == 5:
        options["node_id"] = args[0]
        options["to"] = args[1]
        options["via"] = args[2]
        options["isp"] = args[3]
        options["seed"] = args[4]

    cmd = happy.HappyNodeRoute.HappyNodeRoute(options)
    cmd.start()
