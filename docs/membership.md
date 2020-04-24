# membership
## overview
jdb is entirely decentralized, meaning each node has its own picture of the state of the cluster and who its peers are. it is important for a node to have up-to-date knowledge of the state of its peers so it is able to route requests to the proper node.

there has been a lot of research in this area that has led to some interesting protocols, including Chord, Pastry, and Kademlia. this past year, my friend and I implemented Chord from the paper (or two versions of the paper), so I was pretty familiar with the concepts and goals around these protocols. generally, each node only keeps track of just enough of its peers to allow for O(log(N)) lookups. the idea behind this is to facilitate large clusters with each node only having to maintain minimal routing information.

since jdb is designed is to handle massive web-scale traffic with tight SLA requirements from my side projects, latency was a concern. 


in order to keep track of nodes in the cluster, each node exchanges its own log of node join/leave events with others in the cluster. each node's awareness of the state of the cluster is derived from this log. during this exchange, each node's log is merged with the one it is exchanging with. the node membership log is modeled as a LWW Register. merging 2 LWW Registers relies on globally-ordered timestamps in the add/remove sets, which is not a trivial topic. for these timestamps, a Hybrid Logical Clock (HLC) is used
