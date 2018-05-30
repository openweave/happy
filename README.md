# Nest Labs Happy -- a network topology orchestration tool

## Introduction

Happy simulates complex network topologies. On a single Linux machine, Happy
can create multiple nodes with network stacks that are independent from each
other. Some nodes may be connected to simulated Thread networks, others may
connect to simulated Wi-Fi, WAN (Internet), or cellular networks.

Happy addresses the following use cases:

* Testing of network protocols and other distributed execution
  programs on a single Linux development machine without using hardware.
* Performing automated functional testing across a network.
* Running multiple concurrent, parallel networks on the same system to improve
  testing throughput.

Happy solves these problems by creating network topology abstractions with
minimal user overhead. Complex topologies may be created with a single shell
command call. Happy supports both interactive use and automated scripting.

Use Happy shell commands to set up, test, and debug their code during development.
The same networking configuration and test programs may then be scripted and used
in automated testing.

## Getting Started

The quickest and easiest way to get started with Happy is to go through our
[Getting Started with Happy and Weave
Codelab](https://codelabs.developers.google.com/codelabs/happy-weave-getting-started/#0).
It walks the user through all the Happy fundamentals, including:

* Creating and deleting a topology
* Networking nodes together
* Saving and restoring topologies
* Connecting a topology to the internet
* Weave fundamentals

## Installation

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

### Make

Before using Happy, it must be installed. Running Happy from the
source tree is not supported. To install, run:

    make

This does two things:

* Creates a happy python package at `/usr/local/lib/python2.7/dist-packages`
* Copies happy shell scripts to `/usr/local/bin`

After installation, Happy Python packages can be imported into Python
environment as any other Python module (e.g. `import happy`). Post installation,
all system users can make Happy shell calls. (e.g. `$ happy-state`).

### Verify installation

At this point Happy commands should be visible from the shell. Calling
`happy-state` should return the following:

    $ happy-state
    
    NETWORKS   Name         Type   State                                     Prefixes
    
    NODES      Name    Interface    Type                                          IPs

## Removing Happy

Before removing Happy make sure that all virtual nodes and networks are
deleted. The simplest way of wiping out past Happy work is by calling
`happy-state-delete -a`:

    happy-state-delete -a

To remove Happy itself, call `make uninstall` within the Happy repo and remove
`happy/bin` from the host's `$PATH`:

    make uninstall
    # Delete happy files from ~ (user home directory)
    rm -f ~/.happy_state.json
    rm -f ~/.happy_conf.json
    rm -f ~/.happy_state.json.lock
    cd /usr/local/lib/python2.7/dist-package
    rm -f happy*

## Happy commands

Most Happy commands follow the same basic syntax. Common flags are:

Flag | Description
----|----
`-h --help` | Show help information for the command
`-q --quiet` | Turn off command output
`-a --add` | Create/add; the default action for a command is -a unless otherwise specified
`-d --delete` | Delete; this action must be specified to perform a delete action

For all commands, the short and long flags are interchangeable, and in some instances can
be omitted entirely. For example, all three of these commands are equivalent:

    $ happy-node-join ThreadNode ThreadNetwork
    $ happy-node-join -i ThreadNode -n ThreadNetwork
    $ happy-node-join --id ThreadNode --network ThreadNetwork

If neither `-a` nor `-d` is used, `-a` is assumed. For example, these two commands are
equivalent:

    $ happy-dns onhub 8.8.8.8
    $ happy-dns -a onhub 8.8.8.8

### Usage of sudo

Happy changes the network configuration that is controlled by the Linux kernel.
Since only root can change the kernel configuration, Happy prompts you to enter
the sudo password during operation.

Happy uses the `$SUDO` system environment variable to call sudo. If $SUDO is
not defined, Happy makes a normal `sudo` call. The user can change the `sudo`
command value through `$SUDO`.

## Documentation

Comprehensive end-user documentation, including Setup and Usage guides, are
located at [openweave.io/happy](https://openweave.io/happy).

An architectural overview of Happy can be found in [ARCHITECTURE.md](./ARCHITECTURE.md).
Significant contributions or alterations to the Happy functionality must be accompanied
by documentation within this repository, or submitted as an
[Issue](https://github.com/openweave/happy/issues) for incorporation on openweave.io.

## Want to contribute?

Contributions are welcome and encouraged. See [CONTRIBUTING.md](./CONTRIBUTING.md)
for details.