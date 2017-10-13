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

DEST=/usr/local/bin
SUDO=sudo
PEP8_LINT ?= pep8
PEP8_LINT_ARGS ?= --max-line-length=132

link:
	for f in happy-*.py; do \
		$(SUDO) cp $$f $(DEST)/"$${f%.*}"; \
		$(SUDO) chmod o+rx $(DEST)/"$${f%.*}"; \
	done

unlink:
	for f in happy-*.py; do \
		$(SUDO) rm -f $(DEST)/"$${f%.*}"; \
	done

pretty-check:
	$(PEP8_LINT) $(PEP8_LINT_ARGS) .
