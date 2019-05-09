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
#       A Happy command line utility shows virtual network topology status.
#
#       The command is executed by instantiating and running HappyStatus class.
#

import getopt
import sys

import happy.HappyState
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyState.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hqs:gljuian:e:",
                                   ["help", "quiet", "save=", "graph", "log", "json", "unlock", "id", "all", "node=", "extension="])

    except getopt.GetoptError as err:
        print happy.HappyState.HappyState.__doc__
        print hred(str(err))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print happy.HappyState.HappyState.__doc__
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-s", "--save"):
            options["save"] = a

        elif o in ("-g", "--graph"):
            options["graph"] = True

        elif o in ("-l", "--log"):
            options["log"] = True

        elif o in ("-j", "--json"):
            options["json"] = True

        elif o in ("-u", "--unlock"):
            options["unlock"] = True

        elif o in ("-i", "--id"):
            options["id"] = True

        elif o in ("-a", "--all"):
            options["all"] = True

        elif o in ("-n", "--node"):
            options["node"] = a

        elif o in ("-e", "--extension"):
            options["extension"] = a

        else:
            assert False, "unhandled option"

    if len(args) == 1:
        options["node"] = args[0]

    cmd = happy.HappyState.HappyState(options)
    cmd.start()
