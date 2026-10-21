HOST = "127.0.0.1"

NODES = {
    "A": (HOST, 5001),
    "B": (HOST, 5002),
    "C": (HOST, 5003),
    "D": (HOST, 5004),
    "E": (HOST, 5005)
}

NEIGHBORS = {
    "A": ["B", "C", "D"],
    "B": ["A", "E"],
    "C": ["A", "D", "E"],
    "D": ["A", "C", "E"],
    "E": ["B", "C", "D"]
}



DEFAULT_TTL = 8

FLOOD_PROBABILITY = 0.7


# ------------------------------------------------------------
# FAILURE DETECTION
# ------------------------------------------------------------

HEARTBEAT_INTERVAL = 1.0

NODE_FAILURE_TIMEOUT = 3.0


# ------------------------------------------------------------
# RETRY SETTINGS
#
# If a probabilistic forwarding decision says "do not forward",
# the node can make another independent attempt.
#
# IMPORTANT:
# Every attempt still uses P = 0.7.
#
# Maximum 5 attempts:
#
# Probability of never forwarding after 5 attempts:
#
#       0.3^5 = 0.00243
#
# Therefore probability of at least one successful forwarding:
#
#       1 - 0.3^5 = 0.99757
#
# approximately 99.76%.
# ------------------------------------------------------------

MAX_FORWARD_ATTEMPTS = 5


# ------------------------------------------------------------
# SOCKET SETTINGS
# ------------------------------------------------------------

BUFFER_SIZE = 4096