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
    print("Server version: {}".format(serverver.replace(b"\x00", b"")))
    print("Client version: {}".format(PROTOCOL_VERSION.replace(b"\x00", b"")))
    if serverver != PROTOCOL_VERSION:
        print("Hold on, that's not the right version... Disconnect!")
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return

    known_ids = [x for x in known_messages]
    print("I know of {} message, their ID's are below.".format(len(known_ids)))
    for x in known_ids:
        print(hex(int.from_bytes(x, "big")))
    ids = b"".join(known_ids)

    lenids = int.to_bytes(len(known_ids), 2, "big")

    print("Going to send the length of the known IDS")
    print("As an integer: {}".format(len(known_ids)))
    print("As bytes: {}".format(lenids))
    print(lenids)

    s.send(lenids)

    print("Going to send following data to server")
    print(ids)

    s.sendall(ids)

    print("Known ID's to the server sent")

    data = b""

    server_lenids_bytes = s.recv(2)
    server_lenids = int.from_bytes(server_lenids_bytes, "big")
    server_known_ids = []

    for _ in range(server_lenids):
        nextid = s.recv(32)
        print("got an ID, {}".format(nextid))
        server_known_ids.append(nextid)

    print(server_known_ids)

    print("-"*30)
    print("Okay, both the client and the server know what they need to send")
    print("-"*30)

    client_ids = set(known_ids)
    server_ids = set(server_known_ids)

    print("I, the client know of {} ID's.".format(len(client_ids)))
    print("They are below")
    print()
    for x in client_ids:
        print(x)

    tosend = client_ids - server_ids
    torecv = server_ids - client_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return

    print("I need to send {} messages to the server".format(len(tosend)))
    print("They are below")
    print()
    for x in tosend:
        print(x)

    for msg in tosend:
        msg = known_messages[msg].serialise()
        s.send(int.to_bytes(len(msg), 8, "big"))
        s.sendall(msg)

    print("I am going to be sent {} messages, their ID's:".format(len(torecv)))
    for x in torecv:
        print(x)
    print()

    for _ in range(len(torecv)):
        msglen = int.from_bytes(s.recv(8), "big")
        print("I will be sent a message of len {}".format(msglen))
        msg = s.recv(msglen)
        print("Just got a message, printing it out now")
        print(msg)
        print("Creating message object")
        newmsg = message.from_serialised(msg)
        print(newmsg)
        print("Adding new message object to the set of known messages")
        known_messages[newmsg.msgid] = newmsg

    print("Okay, I'm done getting the server's messages!")

    print("I know of {} messages, they are below".format(len(known_messages)))
    for x in known_messages:
        print(known_messages[x])


def listen(socket):
    conn, addr = s.accept()
    print("I'm really copying this from the tutorial.")
    print("Anyway, {} wanted to say hello.".format(addr))
    clientver = conn.recv(16)
    print("Client is running version {}".format(clientver))
    if clientver != PROTOCOL_VERSION:
        print("That's not the right version!")
        print("Send our version anyway, but expect a disconnect once we do")
        conn.send(PROTOCOL_VERSION)
        conn.close()
        return

    conn.send(PROTOCOL_VERSION)
    print("Version sent")

    client_known_ids = []

    client_lenids_bytes = conn.recv(2)
    client_lenids = int.from_bytes(client_lenids_bytes, "big")
    print("Recieved how many ID's I am about to be sent")
    print("As bytes: {}".format(client_lenids_bytes))
    print("As an integer: {}".format(client_lenids))


    print(client_lenids)
    for _ in range(client_lenids):
        print(_)
        nextid = conn.recv(32)
        print("got an ID, {}".format(nextid))
        client_known_ids.append(nextid)

    print("The client knows of {} messages, their ID's:".format(
        len(client_known_ids)))

    for x in client_known_ids:
        print(b"    " + x)

    # Now do it again, in reverse

    known_ids = [x for x in known_messages]
    print("I know of {} message, their ID's are below.".format(len(known_ids)))
    for x in known_ids:
        print(b"    " + x)

    lenids = len(known_ids)
    lenids_bytes = int.to_bytes(lenids, 2, "big")
    conn.send(lenids_bytes)

    tosend = b"".join(known_ids)
    conn.sendall(tosend)

    print("-"*30)
    print("Okay, both the client and the server know what they need to send")
    print("-"*30)

    server_ids = set(known_ids)
    client_ids = set(client_known_ids)

    print("I, the server know of {} ID's.".format(len(server_ids)))
    print("They are below")
    print()
    for x in server_ids:
        print(x)

    tosend = server_ids - client_ids
    torecv = client_ids - server_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        conn.close()
        return

    print("I need to send {} ID's to the client".format(len(tosend)))
    print("They are below")
    for x in tosend:
        print(x)
    print()

    print("I am going to be SENT {} messages, their ID's:".format(len(torecv)))
    for x in torecv:
        print(x)
    print()

    for _ in range(len(torecv)):
        msglen = int.from_bytes(conn.recv(8), "big")
        print("I will be sent a message of len {}".format(msglen))
        msg = conn.recv(msglen)
        print("Just got a message, printing it out now")
        print(msg)
        print("Creating message object")
        newmsg = message.from_serialised(msg)
        print(newmsg)
        print("Adding new message object to the set of known messages")
        known_messages[newmsg.msgid] = newmsg

    print("Okay, I'm done recieving the client's messages!")

    print("I know of {} messages, they are below".format(len(known_messages)))
    for x in known_messages:
        print(known_messages[x])

    # Now I copy paste and hope for the best!

    for msg in tosend:
        tosend = known_messages[msg].serialise()
        conn.send(int.to_bytes(len(tosend), 8, "big"))
        conn.sendall(tosend)

    print("Sync finished!")
    print()
    print()
    print()
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
