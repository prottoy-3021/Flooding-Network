FLOODING NETWORK PROJECT
========================

Number of nodes: 5

Nodes:
A = 5001
B = 5002
C = 5003
D = 5004
E = 5005


ALGORITHM
---------

The flooding algorithm forwards an incoming packet
to multiple neighboring nodes.

Each packet contains:

1. Packet ID
2. Source
3. Destination
4. Message
5. TTL
6. Path


DUPLICATE DETECTION
-------------------

Every node maintains a set of packet IDs.

If a packet ID has already been processed,
the packet is considered a duplicate and is
not forwarded again.


DYNAMIC FAILURE
---------------

If Node B is stopped during communication,
the packet can still reach Node E through
another available node such as C or D.

No routing table modification is required.


OPTIMIZED FLOODING
------------------

A probabilistic flooding rule is used.

P = 0.7

Each eligible neighbor has a 70 percent probability
of receiving the forwarded packet.

This reduces unnecessary packet transmissions
compared with unrestricted flooding.


LOGGING
-------

The logger records:

- Total packets received
- Unique packets
- Duplicate packets
- Packets forwarded
- Packets delivered