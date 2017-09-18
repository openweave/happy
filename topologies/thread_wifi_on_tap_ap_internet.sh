#!/bin/bash
# Example of Thead, WiFi, and WAN networks, which have:
# - one thread-only device ThreadNode
# - one thread-wifi border_gateway device BorderRouter
# - one access-point router onhub
# - the onhub router is connected to the Internet

happy-network-add HomeThread thread
happy-network-address HomeThread 2001:db8:111:1::

happy-network-add HomeWiFi wifi
happy-network-address HomeWiFi 2001:db8:222:2::
happy-network-address HomeWiFi 10.0.1.0

happy-node-add ThreadNode
happy-node-join --tap ThreadNode HomeThread

happy-node-add BorderRouter
happy-node-join --tap BorderRouter HomeThread
happy-node-join --tap BorderRouter HomeWiFi

happy-node-add --ap onhub
happy-node-join onhub HomeWiFi

happy-network-route HomeThread BorderRouter
happy-network-route --prefix 10.0.1.0 HomeWiFi onhub
happy-network-route --prefix 2001:db8:222:2:: HomeWiFi onhub

weave-fabric-add fab1
weave-node-configure
weave-network-gateway HomeThread BorderRouter

# happy-internet onhub
# happy-dns 172.16.255.1 172.16.255.153 172.16.255.53

# happy-state -s thread_wifi_on_tap_ap_internet.json
