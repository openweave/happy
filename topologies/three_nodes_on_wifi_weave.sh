#!/bin/bash
# Steps to manually build three_nodes_on_wifi_weave.json

happy-node-add node01
happy-node-add node02
happy-node-add node03
happy-network-add Home wifi
happy-network-address Home 2001:db8:1:2::
happy-node-join node01 Home
happy-node-join node02 Home
happy-node-join node03 Home

weave-fabric-add fab1
weave-node-configure

#happy-state -s three_nodes_on_wifi_weave.json
