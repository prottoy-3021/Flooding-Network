
import socket
import sys


from config import (
    NODES,
    DEFAULT_TTL
)


from packet import (
    create_packet,
    encode_packet
)


if len(sys.argv) < 3:

    print()

    print("=" * 70)

    print(
        "FLOODING NETWORK SENDER"
    )

    print("=" * 70)

    print()

    print(
        "Usage:"
    )

    print(
        'python sender.py <SOURCE> '
        '<DESTINATION> [MESSAGE]'
    )

    print()

    print(
        "Example:"
    )

    print(
        'python sender.py A E '
        '"Hello from Node A"'
    )

    print()

    sys.exit(1)


# ============================================================
# SOURCE
# ============================================================

SOURCE = sys.argv[1].upper()


# ============================================================
# DESTINATION
# ============================================================

DESTINATION = sys.argv[2].upper()


# ============================================================
# MESSAGE
# ============================================================

if len(sys.argv) > 3:

    MESSAGE = " ".join(
        sys.argv[3:]
    )

else:

    MESSAGE = (
        "Hello from dynamic flooding network!"
    )


# ============================================================
# VALIDATE SOURCE
# ============================================================

if SOURCE not in NODES:

    print()

    print(
        f"ERROR: Invalid source node '{SOURCE}'."
    )

    print(
        "Valid nodes: A, B, C, D, E"
    )

    sys.exit(1)


# ============================================================
# VALIDATE DESTINATION
# ============================================================

if DESTINATION not in NODES:

    print()

    print(
        f"ERROR: Invalid destination node "
        f"'{DESTINATION}'."
    )

    print(
        "Valid nodes: A, B, C, D, E"
    )

    sys.exit(1)


# ============================================================
# CREATE PACKET
# ============================================================

packet = create_packet(
    SOURCE,
    DESTINATION,
    MESSAGE
)


packet["ttl"] = DEFAULT_TTL

packet["path"] = [
    SOURCE
]


# ============================================================
# SOURCE ADDRESS
# ============================================================

source_ip, source_port = NODES[
    SOURCE
]


# ============================================================
# CREATE UDP SOCKET
# ============================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)


# ============================================================
# DISPLAY INFORMATION
# ============================================================

print()

print("=" * 70)

print(
    "DYNAMIC FLOODING NETWORK SENDER"
)

print("=" * 70)

print(
    f"Source Node      : {SOURCE}"
)

print(
    f"Destination Node : {DESTINATION}"
)

print(
    f"Message          : {MESSAGE}"
)

print(
    f"Packet ID        : "
    f"{packet['packet_id']}"
)

print(
    f"TTL              : {packet['ttl']}"
)

print(
    f"Initial Path     : "
    f"{' -> '.join(packet['path'])}"
)

print(
    f"Injection Address: "
    f"{source_ip}:{source_port}"
)

print("=" * 70)


# ============================================================
# SEND PACKET
# ============================================================

try:

    sock.sendto(
        encode_packet(packet),
        (
            source_ip,
            source_port
        )
    )


    print()

    print(
        f"[SUCCESS] Packet injected "
        f"into Node {SOURCE}."
    )

    print()

    print(
        "Dynamic flooding has started."
    )

    print(
        "P = 0.7 is used for forwarding."
    )

    print()

    print(
        "Check flooding_log.txt for "
        "the complete network log."
    )

    print()


except ConnectionResetError:

    print()

    print(
        "[WARNING] Windows reported "
        "WinError 10054."
    )

    print(
        "Make sure the source node is running."
    )

    print()


except OSError as error:

    if getattr(
        error,
        "winerror",
        None
    ) == 10054:

        print()

        print(
            "[WARNING] WinError 10054."
        )

        print(
            f"Node {SOURCE} may not be running."
        )

        print()

    else:

        print()

        print(
            f"[ERROR] Could not send packet: "
            f"{error}"
        )

        print()


except Exception as error:

    print()

    print(
        f"[ERROR] Could not send packet: "
        f"{error}"
    )

    print()


finally:

    sock.close()