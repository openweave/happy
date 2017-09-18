Nest Labs Happy -- a network topology orchestration tool
==========================================

Introduction
------------

Happy is a tool that builds complex network topologies using Linux
tools. For example, on a local computer Happy can create multiple
nodes that have independent from each other network stacks. Some nodes
may be connected to simulated Thread networks, other may connect to
simulated WiFi, WAN (Internet), and cellular networks.

Happy was designed to address the following problems:

- testing of network protocols and other distributed execution
  programs on a single Linux development machine without using hardware.

- performing automated functional testing across a network.

- running multiple concurrent, parallel networks on the same system to improve
  testing throughput

Happy solves these problems by creating network topology abstractions
with minimal user overhead. Complex topologies may be created with a
single shell command call.  Happy supports both interactive use and
automated scripting.  During development users may prefer to use Happy
shell commands to setup, test, and debug their code.  The same
networking configuration and test programs may then be scripted and
used in the automated testing.

Getting Started
---------------

Happy has a strong dependence on Linux Network Namespaces, and as a
result, is only supported in the Linux environment.

### Prerequisites

    # Mandatory: python-setuptools
    sudo apt-get install python-setuptools
    # Mandatory: Linux bridge utilities
    sudo apt-get install bridge-utils
    # Mandatory: python-lockfile
    sudo apt-get install python-lockfile
    # Mandatory: python-psutil
    sudo apt-get install python-psutil
    # Optional: Graphic Tools
    sudo apt-get install python-networkx
    sudo apt-get install python-matplotlib
    # Optional: Tmux
    sudo apt-get install tmux

### Installation

Before using Happy, it must be installed.  Running Happy from the
source tree is not supported. To install, run:

    make

This does two things:

- creates a happy python package at `/usr/local/lib/python2.7/dist-packages`

- copies happy shell scripts to `/usr/local/bin`

After installation, Happy Python packages can be imported into Python
environment as any other Python module (e.g. `import happy`). Post installation,
all system users can make Happy shell calls. (e.g. `$ happy-state`).

### Checking

At this point Happy commands should be visible from the shell. Calling
`happy-state` should return the following:

    $ happy-state
    
    NETWORKS   Name         Type   State                                     Prefixes
    
    NODES      Name    Interface    Type                                          IPs

### Removing Happy

Before removing happy make sure that all virtual node and networks are
deleted. The simplest way of wiping out happy past work is by calling
`happy-state-delete -a`:

    happy-state-delete -a

To remove happy itself, call make uninstall within happy repo and remove
`happy/bin` from the host's `$PATH`:

    make uninstall
    # Delete happy files from ~ (user home directory)
    rm -f ~/.happy_state.json
    rm -f ~/.happy_conf.json
    rm -f ~/.happy_state.json.lock
    cd /usr/local/lib/python2.7/dist-package
    rm -f happy*

### Limitations and Known Issues

- Happy changes host's network configuration that is controlled by Linux
  kernel. Since only root can change kernel configuration, as a user runs Happy
  once in a while the user needs to enter `sudo` password.  Happy uses system
  environment variable to call `sudo`; specifically, happy calls `sysenv
  $SUDO`. If `$SUDO` is not defined, happy simply makes a `sudo` call. The user
  can change the `sudo` command value through `$SUDO`.

- Happy is using host's Linux tools, therefore it interferes with host's
  networking configuration. As a result, while using Happy, Google Desktop will
  show messages reporting changes in host's network interfaces.

Documentation
-------------

Architectural overview of Happy can be found in
this [document](./ARCHITECTURE.md).  Additional Happy documentation is
maintained on https://github.com/openweave/happy/wiki Significant contributions
or alterations to the Happy functionality must be accompanied by documentation on
the wiki or within this repository.

Contributing to Happy
---------------------

Contributions are welcome and encouraged.
See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

