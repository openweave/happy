# #!/bin/bash
# Steps to manually build three_nodes_on_thread_happy_with_tmux.json

happy-node-add node00
happy-node-add node01
happy-node-add node02
happy-network-add Home Thread
happy-network-address Home 2001:db8:11:22::
happy-node-join node00 Home
happy-node-join node01 Home
happy-node-join node02 Home

weave-fabric-add 13
weave-node-configure

happy-node-tmux -n node00
happy-node-tmux -n node01
happy-node-tmux -n node02

# happy-state -s three_nodes_on_thread_weave_with_tmux
