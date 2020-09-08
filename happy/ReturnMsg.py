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
#       Implements ReturnMsg class.
#
#       ReturnMsg is used to return not only numerical status of
#       success or fail, but allows to return any data structure as well.
#


class ReturnMsg:
    def __init__(self, value=None, data=None):
        self.value = value

        if data is None:
            self.data = None
        elif isinstance(data, dict):
            self.data = data.copy()
        elif isinstance(data, list):
            self.data = data[:]
        else:
            self.data = data

    def Value(self, value=None):
        if value is None:
            return self.value
        else:
            self.data = value

    def Data(self, data=None):
        if data is None:
            return self.data
        elif isinstance(data, dict):
            self.data = data.copy()
        elif isinstance(data, list):
            self.data = data[:]
        else:
            self.data = data
