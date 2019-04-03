#
#    Copyright (c) 2018 Google LLC.
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

# Binaries used by this makefile

DPKG               ?= $(shell which dpkg 2> /dev/null)
MAKE               ?= make
PEP8_LINT          ?= pep8
PEP8_LINT_ARGS     ?= --max-line-length=132
PYTHON             ?= python
PYTHON_VERSION     ?= $(shell $(PYTHON) -c "import sys; sys.stdout.write(sys.version[:3])")
SUDO               ?= sudo

# The list of Debian packages on which Happy depends which must be
# installed before Happy may be used.

DPKG_PREREQUISITES := \
    bridge-utils      \
    net-tools         \
    python-lockfile   \
    python-psutil     \
    python-setuptools \
    $(NULL)

# check-dpkg-prequisite <package>
#
# Determines and verbosely reports whether the specified Debian
# package is installed or not, exiting with the appropriate status.

define check-dpkg-prerequisite
@echo -n "Checking for $(1)...";
@if `$(DPKG) -s $(1) > /dev/null 2>&1`; then \
    echo "ok"; \
else \
    echo "failed"; \
    echo "The package '$(1)' is required and is not installed. Please run 'sudo apt-get install $(1)' to install it."; \
    exit 1; \
fi
endef

check_TARGETS = $(addprefix check-dpkg-,$(DPKG_PREREQUISITES))

check-dpkg-%: $(DPKG)
	$(call check-dpkg-prerequisite,$(*))

all: install

check-prerequisites: $(check_TARGETS)

# If HAPPY_PATH defined, install or uninstall the specific, $HAPPY_PATH,
# location of the Happy package. If HAPPY_PATH is not defined, by default
# install Happy into Python's system with install-system.

install: check-prerequisites
ifeq ($(HAPPY_PATH),)
	$(MAKE) install-system
else
	$(MAKE) install-path
endif

uninstall:
ifeq ($(HAPPY_PATH),)
	$(MAKE) uninstall-system
else
	$(MAKE) uninstall-path
endif

# Install Happy into Python's shared library in a developed version.
# Develop version instead of copying Happy package into /usr/local/lib ...,
# creates a reference to the Happy source directory. This allows a developer
# to modify Happy modules and test them without reinstalling Happpy.

install-develop: check-prerequisites
	# Installing Happy for development
	$(SUDO) $(PYTHON) setup.py develop
	$(MAKE) link

uninstall-develop:
	$(SUDO) $(PYTHON) setup.py develop --uninstall
	$(MAKE) unlink
	$(MAKE) clean

# Install Happy into a user's home directory (~/.local). This allows a user
# to install Happy without requiring root privilages. The installed Happy
# package is only visible to the user that installed it; other same system's
# users cannot find Happy package unless they install it as well.

install-user: check-prerequisites
	# Installing Happy into user home directory
	$(PYTHON) setup.py install --user
	@echo
	@echo "Happy package installed into users ~/.local/lib/*"
	@echo "Happy shell scripts are not installed into the system."
	@echo "To use happy shell scripts, add happy bin/ into PATH."
	@echo

uninstall-user:
	rm -rf ~/.local/lib/python$(PYTHON_VERSION)/site-packages/happy*.egg

# Install Happy into Python system-wide distribution packages. This installation
# requires root privilages. After installation every user in the system can
# use Happy package.

install-system: check-prerequisites
	# Installing Happy
	$(SUDO) $(PYTHON) setup.py install
	$(SUDO) chmod o+r `find /usr/local/lib -name main_config.json`
	$(SUDO) chmod o+r `find /usr/local/lib -name log_config.json`
	$(MAKE) link

uninstall-system:
	$(MAKE) unlink
	$(MAKE) clean
	$(SUDO) rm -rf /usr/local/lib/python$(PYTHON_VERSION)/dist-packages/happy-*egg

# Install Happy package into non-standard location. Because the installed package
# location is not know to Python, the package path must be passed to PYTHON through
# PYTHONPATH environment variable. To install Happy under /some/path run:
# make HAPPY_PATH=/some/path
# This will create /some/path/lib/pythonX.X/site-packages location and install
# the happy package over there.

install-path: check-prerequisites
ifeq ($(HAPPY_PATH),)
	@echo Variable HAPPY_PATH not set. && false
endif
	mkdir -p $(HAPPY_PATH)/lib/python$(PYTHON_VERSION)/site-packages/; \
	export PYTHONPATH="$(HAPPY_PATH)/lib/python$(PYTHON_VERSION)/site-packages/" ;\
	$(PYTHON) setup.py install --prefix=$(HAPPY_PATH)
	@echo
	@echo "Using custom path for a Python package is unusual."
	@echo "Remember to update PYTHONPATH for every environment that will use this package, thus run"
	@echo "export PYTHONPATH=$$PYTHONPATH:"$(HAPPY_PATH)/lib/python$(PYTHON_VERSION)/site-packages/""
	@echo
	$(MAKE) link

uninstall-path:
ifeq ($(HAPPY_PATH),)
	@echo Variable HAPPY_PATH not set. && false
endif
	$(MAKE) unlink
	rm -rf $(HAPPY_PATH)

distribution-build: clean
	# creates a built distribution
	$(PYTHON) setup.py bdist

distribution-source: clean
	# creates a source distribution
	$(PYTHON) setup.py sdist

distribution: distribution-build distribution-source

release: distribution

link:
	$(MAKE) link -C bin

unlink:
	$(MAKE) unlink -C bin

clean:
	$(MAKE) clean -C happy
	$(SUDO) rm -rf *.egg*
	$(SUDO) rm -rf dist
	$(SUDO) rm -rf build

pretty-check:
	$(PEP8_LINT) $(PEP8_LINT_ARGS) .
