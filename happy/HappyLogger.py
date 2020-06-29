#!/usr/bin/env python3

#
#    Copyright (c) 2017 Nest Labs, Inc.
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
#       Implements HappyLogger class that provides logging routines
#

from __future__ import absolute_import
from __future__ import print_function
import logging
import logging.config
import os
import sys
import json


class HostnameFilter(logging.Filter):
    hostname = os.environ.get("HAPPY_HOST", "unknown")

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True

log_config = "conf/log_config.json"
main_config = "conf/main_config.json"


class HappyLogger():

    def __init__(self, opts={}):

        default_happy_path = os.path.dirname(os.path.realpath("%s" % (__file__)))
        default_log_conf_file = default_happy_path + "/" + log_config
        default_main_conf_file = default_happy_path + "/" + main_config

        self.log_conf_file = opts.get("log_conf_file", default_log_conf_file)
        self.main_conf_file = opts.get("main_conf_file", default_main_conf_file)

        self.log_level_file = "DEBUG"
        self.log_level_console = "INFO"

        self.__read_conf()

    def __read_conf(self):
        try:
            with open(self.main_conf_file, 'r') as jfile:
                json_data = jfile.read()
                self.main_conf = json.loads(json_data)

            with open(self.log_conf_file, 'r') as jfile:
                json_data = jfile.read()
                self.log_conf = json.loads(json_data)
        except:
            print("Failed to load config from %s." % (self.log_conf_file))
            sys.exit(1)

        confDict = dict(self.main_conf)
        confDict['state_id'] = self.main_conf['default_state']
        self.log_conf['handlers']['file']['filename'] = self.log_conf['handlers']['file']['filename'] % confDict

        self.log_conf['handlers']['file']['level'] = logging.getLevelName(self.log_level_file)
        self.log_conf['handlers']['stream']['level'] = logging.getLevelName(self.log_level_console)

        logging.config.dictConfig(self.log_conf)
        self.logger = logging.getLogger(__name__)

        h = HostnameFilter()

        try:
            pass
        except ValueError as e:
            emsg = "Failed to load logging configuration: "
            print(emsg)
            print(e)
            sys.exit(1)

        except TypeError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

        except AttributeError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

        except ImportError as e:
            emsg = "Failed to load logging configuration: %d (%s)" % \
                (e.errno, e.strerror)
            print(emsg)
            sys.exit(1)

if __name__ == '__main__':
    opts = {"main_conf_file": None,
            "log_conf_file": None}

    hl = HappyLogger()
