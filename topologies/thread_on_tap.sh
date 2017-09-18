#!/bin/bash
# Example of Thead on TAP network.

happy-network-add HomeThread thread
happy-network-address HomeThread 2001:db8:111:1::

happy-node-add node0
happy-node-add node1
happy-node-add node2

happy-node-join --tap node0 HomeThread
happy-node-join --tap node1 HomeThread
happy-node-join --tap node2 HomeThread

# happy-state -s thread_on_tap.json
