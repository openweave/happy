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
#       A Happy command line utility that modifies user's configuration setup
#
#       The command is executed by instantiating and running HappyConfiguration class.
#

from __future__ import absolute_import
from __future__ import print_function
import getopt
import sys

import happy.HappyConfiguration
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyConfiguration.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hqc:d:k:v:",
                                   ["help", "quiet", "config-type=", "delete=", "key=", "value="])

    except getopt.GetoptError as err:
        print(happy.HappyConfiguration.HappyConfiguration.__doc__)
        print(hred(str(err)))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print(happy.HappyConfiguration.HappyConfiguration.__doc__)
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-d", "--delete"):
            options["delete"] = a

        elif o in ("-k", "--key"):
            options["key"] = a

        elif o in ("-v", "--value"):
            options["value"] = a

        elif o in ("-c", "--config-type"):
            options["config-type"] = a

        else:
            assert False, "unhandled option"

    if len(args) == 1:
        if "=" in args[0]:
            k, v = args[0].split("=")
            options["key"] = k
            options["value"] = v
        else:
            options["key"] = args[0]

    if len(args) == 2:
        options["key"] = args[0]
        options["value"] = args[1]

    cmd = happy.HappyConfiguration.HappyConfiguration(options)
    cmd.start()
