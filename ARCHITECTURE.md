Architecture
------------

Happy models nodes, links and networks:

- nodes are network namespaces.  Processes comprising the node, run within a
  specified network namespace.

- links are network interfaces.  Out of the box, Happy supports L3 (IP)
  interfaces via the `veth` device, L2 interfaces via `tap` and offers the
  ability to reach out to the internet via host's real network interfaces.

- networks are namespaces with an Ethernet bridge running within them.

### Implementation

Happy is a collection of Python modules. Core Happy modules provide abstractions
for:

- managing happy node abstractions (adding/modifying/deleting a node, running a
  set of processes within the node)

- managing links (adding/modifying/deleting links, assigning links to the node
  and to the network, assigning and modifying address assignments)

- managing networks (create/modify/destroy, manage connectivity)

- managing the overall state of the framework in a cohesive fashion

Most of the abstractions that are implemented by Happy modules map
into commands that invoke Linux network tools.

Happy also contains a set of `plugins`.  Plugins wrap a set of
functionality related to a particular technology, for example,
`plugins/weave` contain helpers that wrap various Weave applications
for execution within Happy.

### Shell commands & Classes

There are two ways how a user can build network topologies with
happy. First, a user can call shell commands that trigger Happy to
build virtual nodes and networks. The Happy shell commands allow user
to pass parameters into Happy modules from command line instead of
requiring writing a python script to instantiate and run happy
modules. Second, a user can write a python program that imports Happy
classes and then instantiates classes with desired options. Every
Happy class provides a set of options that allows to configure a
class' instance execution. For example, a `HappyNodeAdd` module, which
creates a virtual node using Linux network namespaces, expects to
receive, as one of the options, the name of the virtual node.

In a python program, one can retrieve a module's options by calling
`option()` function. For example, a python code that retrieves
`HappyNodeAdd` module options, would do:

    module options
    import happy.HappyNodeAdd
    options = happy.HappyNodeAdd.option()

Happy shell commands are stored in happy repository under bin
directory. The implementation of the Happy core modules is under happy
directory. Using the example of `HappyNodeAdd`, we have:

- `bin/happy-node-add.py` -- imports `HappyNodeAdd`, retrieves all default
  option parameters that `HappyNodeAdd` class instance expects and overwrites
  them with those passed from the shell.

- `happy/HappyNodeAdd.py` implements `HappyNodeAdd` class, which after
  instantiating executes its actions after getting called on run() class member
  function.

### State

During Happy execution a lot of things are happening in the
background: networks, links, and nodes are created; then routes and IP
addresses are assigned. All these actions map to a much larger set of
commands that are passed to Linux networking tools. To keep track of
everything that happens due to Happy actions, Happy stores and
carefully maintains its state in a form of a JSON record stored in a
file.  Happy supports coexistence of multiple parallel Happy states;
the choice of which state to use is controlled via the
`HAPPY_STATE_ID` environment variable.  If the variable is not present
in the environment, the framework assumes a default value of `happy`.
The state file for a particular happy configuration is located at
`~/.${HAPPY_STATE_ID}_state.json`, by default in `/.happy_state.json`.

Whenever the a node or a network is created or deleted, the Happy
state file is updated. The state is not only used to keep track of
what is happening but it is also used to ensure that when Happy
modules are executing, either due to calls from shell or invocations
from other programs, the modules can execute safely and correctly. For
example, when `HappyNodeAddress` module tries to assign an IP address to
some node's network interface, Happy state is used to ensure that a
node exist and has an interface, before the IP address assignment
command is called.

One can read the state file and see all the details in a JSON
format. A user-friendly readable summary of the Happy state can be
displayed on a shell by calling happy-state command, which invokes
`HappyState.py` module.

Happy allows users to build and execute tests on multiple independent
network topologies. This feature can be understood as parallel
execution of independent Happy states, where both network topologies
can coexist on the same computer but they do not interfere with each
other and their states are kept separated. Happy keeps track of
parallel states by using state IDs and storing different state records
in separate JSON files. By default, the state ID is set to happy and
thus it is saved in `~/.happy_state.json` file. The state ID can be
changed by exporting system variable `HAPPY_STATE_ID`. For example, we
can create a state called _sunny_ and start by adding a virtual node:

    $ export HAPPY_STATE_ID=sunny
    $ happy-node-add node00
    $ happy-state

    State Name:  sunny

    NETWORKS   Name         Type   State                                     Prefixes

    NODES      Name    Interface    Type                                          IPs
             node00

    $ cat ~/.sunny_state.json
    {
        "node": {
            "node00": {
                "interface": {},
                "process": {},
                "route": {},
                "tmux": {},
                "type": null
            }
        }
    }
    $

### Configuration

Happy has its configuration files under `conf` directory, within happy
repository. There are two main configuration files. First,
`log_config.json` specifies where logging information should be sent
to and how it should be formatted. Be default, syslog receives Happy
logs, but there is also another dedicated backup stream of logs sent to
`/tmp/${HAPPY_STATE_ID}_debug_log.txt`. Happy logs are updated in
real-time, as modules are executing and issue commands to Linux. On
the other hand, the state file is usually updated only after
successful execution of a module. At run-time, a user can see
real-time logs by calling `happy-strace` with `-l` (`l` for logs). Watching
logs in the real-time is very useful in debugging and developing new
features in Happy. For example, we present a transcript of two shell
windows: first one runs `happy-state -l` to display real time
logs, while second one calls `happy-node-add` command with
`node00` parameter.

Happy Logs

    $ happy-state -l
    Happy Runtime Logs. Press <Ctrl-C> to exit.
    tail: cannot open ‘100’ for reading: No such file or directory
    ==> /tmp/happy_debug_log.txt <==
    Happy 2016-02-25 11:04:19,904    DEBUG > Happy [happy]: > sudo ip netns list
    Happy 2016-02-25 11:04:20,040    DEBUG > Happy [happy]: > sudo ip netns add happynode00
    Happy 2016-02-25 11:04:20,173    DEBUG > Happy [happy]: > sudo ip netns list
    Happy 2016-02-25 11:04:20,304    DEBUG > Happy [happy]:      happynode00
    Happy 2016-02-25 11:04:20,305    DEBUG > Happy [happy]: > sudo ip netns exec happynode00 ifconfig lo up

Running Happy From Shell (Add Happy node called _node00_)

    $ happy-node-add node00

The second configuration file that we find in conf directory is
`main_config.json`. This configuration file specifies the default
state ID - happy, and the state environment variable that can
overwrite the state ID - `HAPPY_STATE_ID`.

Finally, there is a third configuration file that allows users to
specify any unconstrained variable that is used by Happy or, more
likely, by a Happy's plugin. The third configuration file is stored in
`~/.happy_conf.json`. That file can be read and edited by invoking
`happy-configuration` command. In Weave plugin we use
`happy-configuration` to enter the path to the compiled Weave's test
apps directory.

Making changes into conf directory files should be considered
carefully. When possible, it is advised to use happy-configuration to
add or modify personal or plugin-specific configurations.

### Processes

Happy runs multiple parallel processes in the context of different
network nodes. The implementation of Happy processes is done in
`HappyProcess*` files. For example, `HappyProcessStart.py` implements
functionality that starts running a program inside of a network node
and returns back to the user without blocking. `HappyProcessStop.py`
stops running a process and `HappyProcessWait.py` allows a different
program to block and wait until some process completes and stops by
itself. The standard output of a process can be retrieved with
`HappyProcessOutput.py` module. When a process starts, it's output is
redirected to a file located in `/tmp` ; HappyProcessOutput finding
the path to correct log file in Happy's state file
(e.g. `~/.happy_state.json`). To inspect details about process
execution, one can retrieve `strace` logs with
`HappyProcessStrace.py`.

### Environment Variables

In automated execution, Happy core modules and its plugins use system
environment variables that allow other tools or processes, e.g. make
check, to pass variables into Happy. The following is the list of
environment variables that have a special meaning for Happy:

- `abs_builddir` : when is found by the Weave plugin it is used to overwrite
  `happy-configuration` `weave_path` variable, thus indicating the path to Weave
  binaries that should be used in execution.

- `HAPPY_STATE_ID` : is the default environment variable ID used as
  `<state_environ>` (see explanation below). By default the value is set to
  "happy".

- `INET_LWIP` : when is found and set to `1` Weave plugin assumes that Weave is
  compiled with `USE_LWIP=1` flag and chooses to build Happy topologies at the
  L2 (TAP with user-level routing) level instead of L3 (veth with kernel routing).

- `USER` : when a code is marked to be executed with existing user's privileges
  instead of as a root, Happy finds user's login from system environment
  variable `USER`.

- `<state_environ>` : is a configurable system environment variable that
  indicates ID of the Happy state. The value of this variable is used to run
  parallel execution of Happy topologies that are independent from each other.

- `happy_host_netif` : specify network interface that should be used to connect
  Happy topology to the real Internet, for example: `export
  happy_host_netif=eth0`.

- `happy_dns` : specify a list of DNS servers that are used when connecting to
  the Internet, for example: `export happy_dns="8.8.8.8"`

- `weave_service_address` : used to specify Salt services address, for example:
  `export weave_service_address="tunnel03.weave01.iad02.integration.nestlabs.com"`.

### Internet connectivity

Happy nodes can be connected to the Internet via host's networking facilities.
The design requirements of Happy dictate that any node from any of the Happy
instances may be connected to the external Internet.  Furthermore, to simulate
the situations with multiple ISPs, Happy provides an abstraction for an ISP.
The Happy ISP leverages a number of existing Happy features:

- Each Happy ISP is modeled with an Ethernet bridge, much like a Happy network.
  The bridge is connected to the host's Internet, and Happy configures
  appropriate NAT entries to route traffic to a subnet reserved for the ISP.
  
- Unlike other Happy nodes and networks, Happy ISP nodes are global entities and
  are named and maintained outside the regular Happy instances.
  
- Each node being connected to the ISP (regardless of what Happy instance the
  node resided in) is treated like any other node in Happy connections.  It is
  connected to the ISP network, and assigned an address.
