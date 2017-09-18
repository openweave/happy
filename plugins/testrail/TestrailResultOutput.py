#!/usr/bin/env python

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
#       Implements TestrailResultOutput class that output the Weave standalone test result to json file for posting testrail
#
import json
import os
from happy.Utils import *

options = {}
options["quiet"] = False
options["file_path"] = None
options["output_data"] = None


def option():
    return options.copy()


class TestrailResultOutput():

    def __init__(self, opts=options):
        self.file_path = opts['file_path']
        self.output_data = opts['output_data']

    def __pre_check(self):

        if not self.output_data:
            emsg = "Missing output Weave test results for testrail."
            self.logger.error("[localhost] TestrailResultOutput: %s" % (emsg))
            if not self.quiet:
                print hred(emsg)
            self.RaiseError(emsg)

        if not self.file_path:
            emsg = "Missing file name of testrail results."
            self.logger.error("[%s] TestrailResultOutput: %s" % (emsg))
            if not self.quiet:
                print hred(emsg)
            self.RaiseError(emsg)

    def __results_output(self):

        try:
            json_data = json.dumps(self.output_data, sort_keys=True, indent=4)
        except Exception:
            print "Failed to save testrail json file: %s" % \
                (self.file_path)
            self.logger.error("calls sys.exit(1)")
            self.exit()

        with open(self.file_path, 'w') as jfile:
            jfile.write(json_data)
            jfile.flush()
            os.fsync(jfile)
        return 0

    def run(self):
        self.__pre_check()

        self.__results_output()
