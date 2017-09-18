#!/bin/bash
# Steps to manually build three_nodes_on_thread_happy.json

happy-node-add node01
happy-node-add node02
happy-node-add node03
happy-network-add Home Thread
happy-network-address Home 2001:db8:1:2::
#virtual node  joins network called Home and get MAC HW address 1.
happy-node-join -m 1 node01 Home
happy-node-join -m 2 node02 Home
happy-node-join -m 3 node03 Home
#virtual node node_01 joins network called Home, eui64 address is 00:00:00:00:00:00:00:01
#happy-node-join -c 00:00:00:00:00:00:00:01 node01 Home
#happy-node-join -c 00:00:00:00:00:00:00:02 node02 Home
#happy-node-join -c 00:00:00:00:00:00:00:03 node03 Home
weave-fabric-add fab1
weave-node-configure -w 18B4300000000004 node01
weave-node-configure -w 18B4300000000005 node02
weave-node-configure -w 18B430000000000A node03

# happy-state -s three_nodes_on_thread_weave.json
