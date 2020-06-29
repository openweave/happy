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
#       A Happy command line utility that enters virtual node's shell.
#
#       The command is executed by instantiating and running HappyShell class.
#

from __future__ import absolute_import
from __future__ import print_function
import getopt
import sys

import happy.HappyShell
from happy.Utils import *

if __name__ == "__main__":
    options = happy.HappyShell.option()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:quc:",
                                   ["help", "id=", "quiet", "user", "command="])

    except getopt.GetoptError as err:
        print(happy.HappyShell.HappyShell.__doc__)
        print(hred(str(err)))
        sys.exit(hred("%s: Failed to parse arguments." % (__file__)))

    for o, a in opts:
        if o in ("-h", "--help"):
            print(happy.HappyShell.HappyShell.__doc__)
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-u", "--user"):
            options["run_as_user"] = True

        elif o in ("-i", "--id"):
            options["node_id"] = a

        elif o in ("-c", "--command"):
            options["command"] = a

        else:
            assert False, "unhandled option"

    if len(args) >= 1:
        if options['node_id'] is None:
            options['node_id'] = args[0]
            del args[0]

    if len(args) >= 1:
        options['command'] = ' '.join(args[:])

    cmd = happy.HappyShell.HappyShell(options)
    cmd.start()
