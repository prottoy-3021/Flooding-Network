import json
import uuid

from config import DEFAULT_TTL


# ============================================================
# CREATE DATA PACKET
# ============================================================

def create_packet(source, destination, message):

    packet = {
        "type": "DATA",

        "packet_id": str(uuid.uuid4()),

        "source": source,

        "destination": destination,

        "message": message,

        "ttl": DEFAULT_TTL,

        "path": [source]
    }

    return packet


# ============================================================
# CREATE HEARTBEAT
# ============================================================

def create_heartbeat(source):

    packet = {
        "type": "HEARTBEAT",
        "node": source
    }

    return packet


# ============================================================
# CREATE HEARTBEAT ACK
# ============================================================

def create_heartbeat_ack(source):

    packet = {
        "type": "HEARTBEAT_ACK",
        "node": source
    }

    return packet


# ============================================================
# ENCODE PACKET
# ============================================================

def encode_packet(packet):

    return json.dumps(packet).encode("utf-8")


# ============================================================
# DECODE PACKET
# ============================================================

def decode_packet(data):

    return json.loads(
        data.decode("utf-8")
    )