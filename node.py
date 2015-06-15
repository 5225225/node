import hashlib
import os
import socket
import sys


POW_DIGITS = 2

PROTOCOL_VERSION = b"!not(OSX<LinuX)"
assert len(PROTOCOL_VERSION) <= 16
PROTOCOL_VERSION = (bytes(16) + PROTOCOL_VERSION)[-16:]
assert len(PROTOCOL_VERSION) == 16

PORT = 3514

VERBOSE = True

known_messages = {}


def can_int(x):
    try:
        f = int(x)
        return True
    except ValueError:
        return False


class POWerror(Exception):
    pass

def mkproof(msgid):
    proof = 0
    while True:
        if hashlib.sha256(
                    int.to_bytes(proof, 8, "big") +
                    msgid
                ).digest().startswith(b"\x00"*POW_DIGITS):
            break
        proof += 1
    return proof


class message:

    def from_serialised(sbytes):
        msgid = sbytes[:32]
        proof = sbytes[32:40]
        gpg = sbytes[40:]

        return message(gpg, int.from_bytes(proof, "big"), msgid)

    def serialise(self):
        x = bytes()

        x += self.msgid
        x += int.to_bytes(self.proof, 8, "big")
        x += self.gpg

        return x

    def __init__(self, gpg, proof=-1, msgid=""):
        if msgid == "":
            self.msgid = hashlib.sha256(gpg).digest()
        else:
            self.msgid = msgid
            expectedmsgid = hashlib.sha256(gpg).digest()
            if not(self.msgid == expectedmsgid):
                raise ValueError("Message ID does not match expected ID")
        if proof == -1:
            self.proof = mkproof(self.msgid)
        else:
            self.proof = proof

        self.gpg = gpg

        proofhash = hashlib.sha256(int.to_bytes(self.proof, 8, "big") + self.msgid).digest()
        if not proofhash.startswith(b"\x00"*POW_DIGITS):
            raise POWerror("Invalid proof when creating message")

    def __repr__(self):
        return "message {}:{}".format(
            hex(self.proof),
            hex(int.from_bytes(self.msgid, "big")))


def sync(ip, port=3514):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Connecting to {}:{}".format(ip, port))
    s.connect((ip, port))
    s.send(PROTOCOL_VERSION)
    serverver = s.recv(16)
    print("Connected to server")
    print("Server version: {}".format(serverver.replace(b"\x00", b"").decode("ascii")))
    print("Client version: {}".format(PROTOCOL_VERSION.replace(b"\x00", b"").decode("ascii")))

    if serverver != PROTOCOL_VERSION:
        print("Hold on, that's not the right version... Disconnect!")
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return

    known_ids = [x for x in known_messages]
    ids = b"".join(known_ids)

    lenids = int.to_bytes(len(known_ids), 2, "big")

    s.send(lenids)

    s.sendall(ids)


    data = b""

    server_lenids_bytes = s.recv(2)
    server_lenids = int.from_bytes(server_lenids_bytes, "big")
    server_known_ids = []

    for _ in range(server_lenids):
        nextid = s.recv(32)
        server_known_ids.append(nextid)

    client_ids = set(known_ids)
    server_ids = set(server_known_ids)

    tosend = client_ids - server_ids
    torecv = server_ids - client_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return

    for msg in tosend:
        msg = known_messages[msg].serialise()
        s.send(int.to_bytes(len(msg), 8, "big"))
        s.sendall(msg)

    for _ in range(len(torecv)):
        msglen = int.from_bytes(s.recv(8), "big")
        msg = s.recv(msglen)
        newmsg = message.from_serialised(msg)
        known_messages[newmsg.msgid] = newmsg

    print("Synced Sucessfully")
    print("Sent the server {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))


def listen(socket):
    conn, addr = s.accept()
    clientver = conn.recv(16)
    print("{} connected".format(addr))
    print("Server version: {}".format(PROTOCOL_VERSION.replace(b"\x00",b"").decode("ascii")))
    print("Client version: {}".format(clientver.replace(b"\x00",b"").decode("ascii")))

    if clientver != PROTOCOL_VERSION:
        print("Disconnecting {} due to mismatching versions".format(addr))
        conn.send(PROTOCOL_VERSION)
        conn.close()
        return

    conn.send(PROTOCOL_VERSION)


    client_known_ids = []

    client_lenids_bytes = conn.recv(2)
    client_lenids = int.from_bytes(client_lenids_bytes, "big")


    for _ in range(client_lenids):
        nextid = conn.recv(32)
        client_known_ids.append(nextid)

    # Now do it again, in reverse

    known_ids = [x for x in known_messages]

    lenids = len(known_ids)
    lenids_bytes = int.to_bytes(lenids, 2, "big")
    conn.send(lenids_bytes)

    tosend = b"".join(known_ids)
    conn.sendall(tosend)


    server_ids = set(known_ids)
    client_ids = set(client_known_ids)

    tosend = server_ids - client_ids
    torecv = client_ids - server_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        conn.close()
        return

    for _ in range(len(torecv)):
        msglen = int.from_bytes(conn.recv(8), "big")
        msg = conn.recv(msglen)
        newmsg = message.from_serialised(msg)
        known_messages[newmsg.msgid] = newmsg

    # Now I copy paste and hope for the best!

    for msg in tosend:
        send = known_messages[msg].serialise()
        conn.send(int.to_bytes(len(send), 8, "big"))
        conn.sendall(send)

    print("Synced sucessfuly")
    print("Sent the server {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))
    print()

if sys.argv[1] == "SELFTEST":
    with open("test", "rb") as f:
        gpg = f.read()
        msg = message(gpg)
        serl = msg.serialise()
        msg2 = message.from_serialised(serl)

        assert msg.serialise() == msg2.serialise()

for path in os.listdir("both"):
    with open("both/" + path, "rb") as f:
        m = message(f.read())
        known_messages[m.msgid] = m

if sys.argv[1] == "SERVER":
    for path in os.listdir("server"):
        with open("server/" + path, "rb") as f:
            m = message(f.read())
            known_messages[m.msgid] = m
    print("Ready")
    print()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", PORT))
    s.listen(5)
    while True:
        listen(s)

if sys.argv[1] == "CLIENT":
    for path in os.listdir("client"):
        with open("client/" + path, "rb") as f:
            m = message(f.read())
            known_messages[m.msgid] = m

    sync("localhost")
