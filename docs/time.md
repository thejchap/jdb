# time
## transactions
local transaction commit timestamps are represented as a monotonically increasing integer `0 < ts < MAX_UINT_64`
## peers
in order to keep track of nodes in the cluster, each node exchanges its own log of node join/leave events with others in the cluster. each node's awareness of the state of the cluster is derived from this log. during this exchange, each node's log is merged with the one it is exchanging with. the node membership log is modeled as a LWW Register. merging 2 LWW Registers relies on globally-ordered timestamps in the add/remove sets, which is not a trivial topic. for these timestamps, a Hybrid Logical Clock (HLC) is used