#!/usr/bin/env python3

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
#       A Happy command line utility through which a virtual node joins the Internet.
#
#       The command is executed by instantiating and running HappyInternet class.
#

from __future__ import absolute_import
from __future__ import print_function
import getopt
import sys

import happy.HappyInternet
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyInternet.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hn:qadf:s:e:",
                                   ["help", "node=", "quiet", "add", "delete", "interface=", "isp=", "seed="])

    except getopt.GetoptError as err:
        print(happy.HappyInternet.HappyInternet.__doc__)
        print(hred(str(err)))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print(happy.HappyInternet.HappyInternet.__doc__)
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-a", "--add"):
            options["add"] = True

        elif o in ("-d", "--delete"):
            options["delete"] = True

        elif o in ("-f", "--interface"):
            options["iface"] = a

        elif o in ("-s", "--isp"):
            options["isp"] = a

        elif o in ("-e", "--seed"):
            options["seed"] = a

        elif o in ("-n", "--node"):
            options["node_id"] = a

        else:
            assert False, "unhandled option"

    cmd = happy.HappyInternet.HappyInternet(options)
    cmd.start()
