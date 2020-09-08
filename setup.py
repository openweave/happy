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
from __future__ import absolute_import
import os
from setuptools import find_packages, setup

exec(open("happy/version.py").read())

here = os.path.abspath(os.path.dirname(__file__))

long_description = open(os.path.join(here, 'README.md')).read()

setup(name="happy",
      version=__version__,

      description="Network topology orchestration tool",

      long_description=long_description,

      author="Nest Labs, Inc.",

      platforms=["Linux"],

      classifiers=[
          "Development Status :: 5 - Production/Stable",

          "License :: OSI Approved :: Apache Software License",

          "Intended Audience :: Developers",
          "Intended Audience :: Education",

          "Operating System :: POSIX :: Linux",

          "Topic :: Software Development :: Testing",
          "Topic :: Software Development :: Embedded Systems",
          "Topic :: System :: Emulators",
          "Topic :: System :: Networking"
      ],

      license="Apache",

      url="https://github.com/openweave/happy/",

      packages=find_packages(),

      package_data={'happy': ['conf/log_config.json', 'conf/main_config.json']},
      )
