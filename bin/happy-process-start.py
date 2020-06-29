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
#       A Happy command line utility that runs a daemon within virtual node.
#
#       The command is executed by instantiating and running HappyProcessStart class.
#

from __future__ import absolute_import
from __future__ import print_function
import getopt
import sys

import happy.HappyProcessStart
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyProcessStart.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:qt:se:",
                                   ["help", "id=", "quiet", "tag=", "strace", "env="])

    except getopt.GetoptError as err:
        print(happy.HappyProcessStart.HappyProcessStart.__doc__)
        print(hred(str(err)))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print(happy.HappyProcessStart.HappyProcessStart.__doc__)
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-i", "--id"):
            options["node_id"] = a

        elif o in ("-t", "--tag"):
            options["tag"] = a

        elif o in ("-s", "--strace"):
            options["strace"] = True

        elif o in ("-e", "--env"):
            options["env"] = a

        else:
            assert False, "unhandled option"

    if len(args) > 2 and options["node_id"] is None and options["tag"] is None:
        options["node_id"] = args[0]
        options["tag"] = args[1]
        options["command"] = " ".join(args[2:])
    else:
        options["command"] = " ".join(args[:])

    if options["env"]:
        dic = {}
        # convert the string to a dictionary
        for var in options["env"].split():
            lh, rh = var.split("=")
            dic[lh] = rh
        options["env"] = dic

    cmd = happy.HappyProcessStart.HappyProcessStart(options)
    cmd.start()
