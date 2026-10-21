import socket
import sys
import random
import threading
import time


from config import (
    NODES,
    NEIGHBORS,
    DEFAULT_TTL,
    FLOOD_PROBABILITY,
    HEARTBEAT_INTERVAL,
    NODE_FAILURE_TIMEOUT,
    MAX_FORWARD_ATTEMPTS,
    BUFFER_SIZE
)


from packet import (
    decode_packet,
    encode_packet,
    create_heartbeat,
    create_heartbeat_ack
)


from logger import Logger


# ============================================================
# CHECK COMMAND LINE
# ============================================================

if len(sys.argv) < 2:

    print()

    print("=" * 70)

    print("DYNAMIC FLOODING NETWORK")

    print("=" * 70)

    print()

    print("Usage:")

    print("python node.py A")

    print("python node.py B")

    print("python node.py C")

    print("python node.py D")

    print("python node.py E")

    print()

    sys.exit(1)


# ============================================================
# NODE NAME
# ============================================================

NODE_NAME = sys.argv[1].upper()


# ============================================================
# VALIDATE NODE
# ============================================================

if NODE_NAME not in NODES:

    print()

    print(
        f"ERROR: Invalid node '{NODE_NAME}'."
    )

    print(
        "Valid nodes are: A, B, C, D, E"
    )

    sys.exit(1)


# ============================================================
# NODE ADDRESS
# ============================================================

MY_IP, PORT = NODES[NODE_NAME]


# ============================================================
# ORIGINAL NEIGHBORS
# ============================================================

ORIGINAL_NEIGHBORS = NEIGHBORS[NODE_NAME]


# ============================================================
# CREATE UDP SOCKET
# ============================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)


# ============================================================
# ALLOW SOCKET REUSE
# ============================================================

sock.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)


# ============================================================
# BIND SOCKET
# ============================================================

try:

    sock.bind(
        (MY_IP, PORT)
    )

except OSError as error:

    print()

    print("=" * 70)

    print(
        f"ERROR: Could not start Node {NODE_NAME}"
    )

    print("=" * 70)

    print(
        f"Address: {MY_IP}:{PORT}"
    )

    print(
        f"Details: {error}"
    )

    print()

    sock.close()

    sys.exit(1)


# ============================================================
# CREATE LOGGER
# ============================================================

logger = Logger(
    NODE_NAME
)


# ============================================================
# PACKETS ALREADY PROCESSED
# ============================================================

seen_packets = set()


# ============================================================
# LAST HEARTBEAT RECEIVED FROM EACH NEIGHBOR
# ============================================================

last_seen = {}

for neighbor in ORIGINAL_NEIGHBORS:

    last_seen[neighbor] = time.time()


# ============================================================
# FAILED NODES
#
# IMPORTANT:
#
# This is NOT a routing table.
#
# It is temporary runtime failure information.
# ============================================================

failed_nodes = set()


# ============================================================
# THREAD LOCK
# ============================================================

status_lock = threading.Lock()


# ============================================================
# STARTUP INFORMATION
# ============================================================

print()

print("=" * 70)

print(
    f"NODE {NODE_NAME} STARTED"
)

print("=" * 70)

print(
    f"IP Address            : {MY_IP}"
)

print(
    f"UDP Port              : {PORT}"
)

print(
    f"Original Neighbors    : "
    f"{ORIGINAL_NEIGHBORS}"
)

print(
    f"Flood Probability     : "
    f"{FLOOD_PROBABILITY}"
)

print(
    f"Maximum Attempts      : "
    f"{MAX_FORWARD_ATTEMPTS}"
)

print(
    f"Heartbeat Interval    : "
    f"{HEARTBEAT_INTERVAL} seconds"
)

print(
    f"Failure Timeout       : "
    f"{NODE_FAILURE_TIMEOUT} seconds"
)

print(
    "Windows UDP 10054     : HANDLED"
)

print(
    "Shared Log            : flooding_log.txt"
)

print("=" * 70)

print(
    "Waiting for packets..."
)

print()


logger.write(
    NODE_NAME,
    f"Node started on {MY_IP}:{PORT}"
)

logger.write(
    NODE_NAME,
    f"Original neighbors: {ORIGINAL_NEIGHBORS}"
)


# ============================================================
# GET CURRENT ACTIVE NEIGHBORS
# ============================================================

def get_active_neighbors():

    with status_lock:

        active_neighbors = []

        for neighbor in ORIGINAL_NEIGHBORS:

            if neighbor not in failed_nodes:

                active_neighbors.append(
                    neighbor
                )

        return active_neighbors


# ============================================================
# MARK NODE AS FAILED
# ============================================================

def mark_node_failed(node):

    with status_lock:

        if node in failed_nodes:

            return

        failed_nodes.add(
            node
        )


    logger.failed_node_detected()


    active_neighbors = get_active_neighbors()


    print()

    print("!" * 70)

    print(
        "[DYNAMIC FAILURE DETECTED]"
    )

    print(
        f"Node {node} is not responding."
    )

    print(
        f"Node {node} removed from "
        f"active flooding neighbors."
    )

    print(
        f"Active neighbors of Node {NODE_NAME}: "
        f"{active_neighbors}"
    )

    print("!" * 70)

    print()


    logger.write(
        NODE_NAME,
        f"DYNAMIC FAILURE DETECTED: Node {node}"
    )

    logger.write(
        NODE_NAME,
        f"Active neighbors after failure: "
        f"{active_neighbors}"
    )


# ============================================================
# MARK NODE AS ALIVE AGAIN
# ============================================================

def mark_node_alive(node):

    recovered = False


    with status_lock:

        if node in failed_nodes:

            failed_nodes.remove(
                node
            )

            recovered = True


    if recovered:

        print()

        print(
            f"[TOPOLOGY RECOVERY] "
            f"Node {node} is responding again."
        )

        print()


        logger.write(
            NODE_NAME,
            f"TOPOLOGY RECOVERY: Node {node}"
        )


# ============================================================
# UPDATE NEIGHBOR HEARTBEAT TIME
# ============================================================

def update_neighbor_alive(node):

    if node not in ORIGINAL_NEIGHBORS:

        return


    with status_lock:

        last_seen[node] = time.time()


    mark_node_alive(
        node
    )


# ============================================================
# SEND HEARTBEAT
# ============================================================

def send_heartbeat(neighbor):

    neighbor_ip, neighbor_port = NODES[
        neighbor
    ]


    heartbeat = create_heartbeat(
        NODE_NAME
    )


    try:

        sock.sendto(
            encode_packet(heartbeat),
            (
                neighbor_ip,
                neighbor_port
            )
        )


    except ConnectionResetError:

        # ----------------------------------------------------
        # Windows may report connection reset when a UDP
        # destination does not exist.
        #
        # DO NOT terminate this node.
        # ----------------------------------------------------

        logger.write(
            NODE_NAME,
            f"Heartbeat connection reset for "
            f"Node {neighbor}"
        )


    except OSError as error:

        # ----------------------------------------------------
        # Specifically handle WinError 10054.
        # ----------------------------------------------------

        if getattr(
            error,
            "winerror",
            None
        ) == 10054:

            logger.write(
                NODE_NAME,
                f"Heartbeat WinError 10054 for "
                f"Node {neighbor}"
            )

        else:

            logger.write(
                NODE_NAME,
                f"Heartbeat socket error for "
                f"Node {neighbor}: {error}"
            )


    except Exception as error:

        logger.write(
            NODE_NAME,
            f"Heartbeat error for "
            f"Node {neighbor}: {error}"
        )


# ============================================================
# HEARTBEAT SENDER
# ============================================================

def heartbeat_sender():

    while True:

        # ----------------------------------------------------
        # Only send heartbeats to currently active nodes.
        # ----------------------------------------------------

        active_neighbors = get_active_neighbors()


        for neighbor in active_neighbors:

            send_heartbeat(
                neighbor
            )


        time.sleep(
            HEARTBEAT_INTERVAL
        )


# ============================================================
# FAILURE MONITOR
# ============================================================

def failure_monitor():

    while True:

        current_time = time.time()


        for neighbor in ORIGINAL_NEIGHBORS:

            with status_lock:

                last_time = last_seen[
                    neighbor
                ]


            elapsed = (
                current_time - last_time
            )


            if elapsed > NODE_FAILURE_TIMEOUT:

                mark_node_failed(
                    neighbor
                )


        time.sleep(
            0.5
        )


# ============================================================
# PROBABILISTIC FORWARDING
# ============================================================
#
# Every forwarding decision uses:
#
#       P = 0.7
#
# We NEVER change it to 1.0.
#
# If the random value is > 0.7, the attempt is skipped.
#
# Up to MAX_FORWARD_ATTEMPTS are allowed.
# ============================================================

def probabilistic_send(
    packet,
    neighbor
):

    for attempt in range(
        1,
        MAX_FORWARD_ATTEMPTS + 1
    ):

        # ----------------------------------------------------
        # Check if neighbor has failed
        # ----------------------------------------------------

        with status_lock:

            if neighbor in failed_nodes:

                print()

                print(
                    f"[FAILED NODE SKIP] "
                    f"Node {neighbor} is unavailable."
                )


                logger.write(
                    NODE_NAME,
                    f"Skipped failed Node {neighbor}"
                )


                return False


        # ----------------------------------------------------
        # Generate random number
        # ----------------------------------------------------

        random_value = random.random()


        logger.forwarding_attempt()


        print()

        print(
            f"[P=0.7 DECISION] "
            f"{NODE_NAME} -> {neighbor}"
        )

        print(
            f"Attempt       : {attempt}"
        )

        print(
            f"Random value  : {random_value:.4f}"
        )

        print(
            f"Required      : <= {FLOOD_PROBABILITY}"
        )


        # ----------------------------------------------------
        # FORWARD
        # ----------------------------------------------------

        if random_value <= FLOOD_PROBABILITY:

            neighbor_ip, neighbor_port = NODES[
                neighbor
            ]


            try:

                sock.sendto(
                    encode_packet(packet),
                    (
                        neighbor_ip,
                        neighbor_port
                    )
                )


                logger.forwarded_packet()


                print(
                    f"[FORWARD SUCCESS] "
                    f"{NODE_NAME} -> {neighbor}"
                )


                logger.write(
                    NODE_NAME,
                    f"Forwarded packet "
                    f"{packet['packet_id']} "
                    f"to Node {neighbor} "
                    f"using P=0.7 "
                    f"attempt={attempt}"
                )


                return True


            except ConnectionResetError:

                print(
                    f"[UDP WARNING] "
                    f"Connection reset while sending "
                    f"to Node {neighbor}"
                )


                logger.write(
                    NODE_NAME,
                    f"Connection reset while sending "
                    f"to Node {neighbor}"
                )


                return False


            except OSError as error:

                if getattr(
                    error,
                    "winerror",
                    None
                ) == 10054:

                    print(
                        f"[UDP WARNING] "
                        f"WinError 10054 while sending "
                        f"to Node {neighbor}"
                    )


                    logger.write(
                        NODE_NAME,
                        f"WinError 10054 while sending "
                        f"to Node {neighbor}"
                    )


                    return False


                print(
                    f"[SEND ERROR] "
                    f"{error}"
                )


                logger.write(
                    NODE_NAME,
                    f"Send error to Node "
                    f"{neighbor}: {error}"
                )


                return False


            except Exception as error:

                print(
                    f"[SEND ERROR] "
                    f"{error}"
                )


                logger.write(
                    NODE_NAME,
                    f"Send error to Node "
                    f"{neighbor}: {error}"
                )


                return False


        # ----------------------------------------------------
        # PROBABILISTIC DROP
        # ----------------------------------------------------

        else:

            logger.probabilistic_drop()


            print(
                f"[PROBABILISTIC DROP] "
                f"{NODE_NAME} did not forward "
                f"to {neighbor}"
            )


            logger.write(
                NODE_NAME,
                f"Probabilistic drop for packet "
                f"{packet['packet_id']} "
                f"toward Node {neighbor} "
                f"attempt={attempt}"
            )


    # --------------------------------------------------------
    # ALL PROBABILISTIC ATTEMPTS FAILED
    # --------------------------------------------------------

    print()

    print(
        f"[FORWARDING ABANDONED] "
        f"{NODE_NAME} -> {neighbor}"
    )

    print(
        f"All {MAX_FORWARD_ATTEMPTS} "
        f"probabilistic attempts failed."
    )


    logger.write(
        NODE_NAME,
        f"All {MAX_FORWARD_ATTEMPTS} "
        f"probabilistic attempts failed "
        f"toward Node {neighbor}"
    )


    return False


# ============================================================
# FLOOD PACKET
# ============================================================

def flood_packet(
    packet,
    previous_node
):

    # --------------------------------------------------------
    # Decrease TTL
    # --------------------------------------------------------

    packet["ttl"] -= 1


    # --------------------------------------------------------
    # TTL EXPIRED
    # --------------------------------------------------------

    if packet["ttl"] <= 0:

        print()

        print(
            f"[TTL DROP] "
            f"Packet {packet['packet_id']} expired."
        )


        logger.write(
            NODE_NAME,
            f"TTL expired for packet "
            f"{packet['packet_id']}"
        )


        return


    # --------------------------------------------------------
    # Get active neighbors
    # --------------------------------------------------------

    active_neighbors = get_active_neighbors()


    print()

    print("=" * 70)

    print(
        f"[DYNAMIC FLOODING] Node {NODE_NAME}"
    )

    print(
        f"Active neighbors: {active_neighbors}"
    )

    print("=" * 70)


    logger.write(
        NODE_NAME,
        f"Active neighbors: {active_neighbors}"
    )


    # --------------------------------------------------------
    # Forward to each eligible neighbor
    # --------------------------------------------------------

    for neighbor in active_neighbors:

        # ----------------------------------------------------
        # Do not immediately send back to sender.
        # ----------------------------------------------------

        if neighbor == previous_node:

            continue


        # ----------------------------------------------------
        # Do not create a cycle.
        # ----------------------------------------------------

        if neighbor in packet["path"]:

            continue


        # ----------------------------------------------------
        # Create a separate copy for this branch.
        # ----------------------------------------------------

        new_packet = packet.copy()


        new_packet["path"] = (
            packet["path"].copy()
        )


        new_packet["path"].append(
            neighbor
        )


        # ----------------------------------------------------
        # P = 0.7 forwarding
        # ----------------------------------------------------

        probabilistic_send(
            new_packet,
            neighbor
        )


# ============================================================
# START HEARTBEAT THREAD
# ============================================================

heartbeat_thread = threading.Thread(
    target=heartbeat_sender,
    daemon=True
)

heartbeat_thread.start()


# ============================================================
# START FAILURE MONITOR
# ============================================================

failure_thread = threading.Thread(
    target=failure_monitor,
    daemon=True
)

failure_thread.start()


# ============================================================
# MAIN RECEIVE LOOP
# ============================================================

try:

    while True:

        # ====================================================
        # RECEIVE UDP PACKET
        # ====================================================
        #
        # IMPORTANT WINDOWS FIX:
        #
        # WinError 10054 must NOT terminate the node.
        # ====================================================

        try:

            data, address = sock.recvfrom(
                BUFFER_SIZE
            )


        except ConnectionResetError:

            print()

            print(
                "[UDP WARNING] "
                "WinError 10054 / connection reset."
            )

            print(
                "A UDP neighbor may be offline."
            )

            print(
                f"Node {NODE_NAME} continues running."
            )

            logger.write(
                NODE_NAME,
                "WinError 10054 received; "
                "node continues running"
            )

            continue


        except OSError as error:

            # ------------------------------------------------
            # WINDOWS ERROR 10054
            # ------------------------------------------------

            if getattr(
                error,
                "winerror",
                None
            ) == 10054:

                print()

                print(
                    "[UDP WARNING] "
                    "WinError 10054 detected."
                )

                print(
                    "A neighboring node may be offline."
                )

                print(
                    f"Node {NODE_NAME} continues running."
                )


                logger.write(
                    NODE_NAME,
                    "WinError 10054 detected; "
                    "node continues running"
                )


                continue


            # ------------------------------------------------
            # OTHER SOCKET ERROR
            # ------------------------------------------------

            print()

            print(
                f"[SOCKET ERROR] {error}"
            )


            logger.write(
                NODE_NAME,
                f"Socket error: {error}"
            )


            continue


        # ====================================================
        # DECODE PACKET
        # ====================================================

        try:

            packet = decode_packet(
                data
            )

        except Exception as error:

            print(
                f"[INVALID PACKET] {error}"
            )

            logger.write(
                NODE_NAME,
                f"Invalid packet received: {error}"
            )

            continue


        # ====================================================
        # PACKET TYPE
        # ====================================================

        packet_type = packet.get(
            "type",
            "DATA"
        )


        # ====================================================
        # HEARTBEAT
        # ====================================================

        if packet_type == "HEARTBEAT":

            sender_node = packet.get(
                "node"
            )


            if sender_node in ORIGINAL_NEIGHBORS:

                update_neighbor_alive(
                    sender_node
                )


                # --------------------------------------------
                # Send heartbeat acknowledgement
                # --------------------------------------------

                ack = create_heartbeat_ack(
                    NODE_NAME
                )


                sender_ip, sender_port = NODES[
                    sender_node
                ]


                try:

                    sock.sendto(
                        encode_packet(ack),
                        (
                            sender_ip,
                            sender_port
                        )
                    )


                except ConnectionResetError:

                    logger.write(
                        NODE_NAME,
                        f"Heartbeat ACK connection reset "
                        f"for Node {sender_node}"
                    )


                except OSError as error:

                    logger.write(
                        NODE_NAME,
                        f"Heartbeat ACK error for "
                        f"Node {sender_node}: {error}"
                    )


            continue


        # ====================================================
        # HEARTBEAT ACK
        # ====================================================

        if packet_type == "HEARTBEAT_ACK":

            sender_node = packet.get(
                "node"
            )


            if sender_node in ORIGINAL_NEIGHBORS:

                update_neighbor_alive(
                    sender_node
                )


            continue


        # ====================================================
        # DATA PACKET
        # ====================================================

        packet_id = packet.get(
            "packet_id"
        )

        source = packet.get(
            "source"
        )

        destination = packet.get(
            "destination"
        )

        message = packet.get(
            "message"
        )


        # ====================================================
        # FIND PREVIOUS NODE
        # ====================================================

        previous_node = None


        sender_ip = address[0]

        sender_port = address[1]


        for name, node_address in NODES.items():

            ip, port = node_address


            if (
                ip == sender_ip
                and
                port == sender_port
            ):

                previous_node = name

                break


        # ====================================================
        # COUNT RECEIVED
        # ====================================================

        logger.received_packet()


        print()

        print("-" * 70)

        print(
            f"[RECEIVED] Node {NODE_NAME}"
        )

        print(
            f"Packet ID     : {packet_id}"
        )

        print(
            f"Source        : {source}"
        )

        print(
            f"Destination   : {destination}"
        )

        print(
            f"Message       : {message}"
        )

        print(
            f"Previous Node : {previous_node}"
        )

        print(
            f"TTL           : {packet.get('ttl')}"
        )

        print(
            f"Path          : "
            f"{' -> '.join(packet.get('path', []))}"
        )

        print("-" * 70)


        logger.write(
            NODE_NAME,
            f"Received packet {packet_id} "
            f"from Node {previous_node}"
        )


        # ====================================================
        # DUPLICATE CHECK
        # ====================================================

        if packet_id in seen_packets:

            logger.duplicate_packet()


            print(
                "[DUPLICATE] "
                f"Packet {packet_id} already processed."
            )


            logger.write(
                NODE_NAME,
                f"Duplicate packet received: "
                f"{packet_id}"
            )


            continue


        # ====================================================
        # MARK UNIQUE
        # ====================================================

        seen_packets.add(
            packet_id
        )


        logger.unique_packet()


        logger.write(
            NODE_NAME,
            f"Unique packet received: "
            f"{packet_id}"
        )


        # ====================================================
        # DESTINATION REACHED
        # ====================================================

        if NODE_NAME == destination:

            logger.delivered_packet()


            print()

            print("*" * 70)

            print(
                "*** PACKET DELIVERED ***"
            )

            print(
                f"Source      : Node {source}"
            )

            print(
                f"Destination : Node {destination}"
            )

            print(
                f"Message     : {message}"
            )

            print(
                f"Path        : "
                f"{' -> '.join(packet['path'])}"
            )

            print(
                f"TTL         : {packet['ttl']}"
            )

            print("*" * 70)

            print()


            logger.write(
                NODE_NAME,
                f"Packet delivered: {packet_id} "
                f"Path: {' -> '.join(packet['path'])}"
            )


            continue


        # ====================================================
        # CONTINUE FLOODING
        # ====================================================

        flood_packet(
            packet,
            previous_node
        )


# ============================================================
# CTRL+C SHUTDOWN
# ============================================================

except KeyboardInterrupt:

    print()

    print(
        f"Node {NODE_NAME} shutting down..."
    )


    logger.write(
        NODE_NAME,
        "Node shutting down"
    )


    logger.print_statistics()


    sock.close()


# ============================================================
# UNEXPECTED ERROR
# ============================================================

except Exception as error:

    print()

    print(
        f"[ERROR] Node {NODE_NAME}: {error}"
    )


    logger.write(
        NODE_NAME,
        f"Unexpected error: {error}"
    )


    logger.print_statistics()


    sock.close()