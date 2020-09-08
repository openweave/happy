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

from __future__ import absolute_import
import time

##
#    @file
#       Provides general, low-level utilities used in software implementing Happy.
#


##
#    Formats input string to print in Red on terminal.
#
#    @param[in]  txt     A string or object that can be coverted to string.
#
#    @return     string with prefixed and suffixed ASCII color formatting.
#
def hred(txt):
    return '\033[31m' + str(txt) + '\033[0m'


##
#    Formats input string to print in Green on terminal.
#
#    @param[in]  txt     A string or object that can be coverted to string.
#
#    @return     string with prefixed and suffixed ASCII color formatting.
#
def hgreen(txt):
    return '\033[32m' + str(txt) + '\033[0m'


##
#    Formats input string to print in Yellow on terminal.
#
#    @param[in]  txt     A string or object that can be coverted to string.
#
#    @return     string with prefixed and suffixed ASCII color formatting.
#
def hyellow(txt):
    return '\033[33m' + str(txt) + '\033[0m'


##
#    Formats input string to print in Blue on terminal.
#
#    @param[in]  txt     A string or object that can be coverted to string.
#
#    @return     string with prefixed and suffixed ASCII color formatting.
#
def hblue(txt):
    return '\033[34m' + str(txt) + '\033[0m'


##
#    Delays execution of a program by sec seconds.
#
#    @param[in]  sec    A number of seconds to delay execution by.
#
#    @return     none
#
def delayExecution(sec):
    time.sleep(sec)
