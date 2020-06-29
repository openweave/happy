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
#       install all necessary python modules for all weave happy tests
#
from __future__ import absolute_import
import subprocess
import sys
import pip


def pip_install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# apis in protobuf and google-api-python-client varies a lot for different version,
# we should == to make sure version for the above modules is working
required_packages = [
    'requests==2.9.1',
    'pexpect==4.6.0',
    'protobuf==3.0.0b2',
    'googleapis-common-protos==1.1.0',
    'grpcio-tools==0.14.0',
    'Cython==0.25.2',
    'google-api-python-client==1.5.2',
    'gcloud==0.18.1',
    'lockfile==0.12.2',
    'grpcio==1.3.5',
    'psutil==1.2.1',
    'wheel==0.34.2']

for package in required_packages:
    pip_install(package)
