import base64
import hashlib
import json
import os
import socket
import sys
import random


POW_DIGITS = 1

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


def convmsg(pgpmsg, proof=-1):
    msg = {}
    msg["gpg"] = base64.b64encode(gpgtobytes(pgpmsg))
    if proof == -1:
        msg["msgid"] = hashlib.sha256(msg["gpg"]).hexdigest().encode("ascii")
        x = 0
        while True:
            if hashlib.sha256(
                    str(x).encode("ascii") +
                    b":" +
                    msg["msgid"]).hexdigest().startswith("0"*POW_DIGITS):
                break
            x += 1
        msg["proof"] = x
    else:
        msg["proof"] = proof
    msg["gpg"] = msg["gpg"].decode("ascii")
    msg["msgid"] = msg["msgid"].decode("ascii")
    return message(json.dumps(msg))


class message:

    def serialise(self):
        return json.dumps({
            "msgid": self.msgid,
            "proof": str(self.proof),
            "gpg": base64.b64encode(self.gpgmsg).decode("ascii"),
        })

    def __init__(self, messagejson):
        x = json.loads(messagejson)
        self.msgid = x["msgid"]
        expectedmsgid = hashlib.sha256(x["gpg"].encode("ascii")).hexdigest()
        if not(self.msgid == expectedmsgid):
            raise ValueError("Message ID does not match expected ID")
        self.gpgmsg = base64.b64decode(x["gpg"])
        self.proof = x["proof"]

        proofhash = hashlib.sha256("{}:{}".format(
            self.proof
            self.msgid
        ).encode("ascii"))
        if not proofhash.startswith("0"*POW_DIGITS):
            raise POWerror("Invalid proof when creating message")

    def __repr__(self):
        return "message {}:{}".format(self.proof, self.msgid)


def gpgtobytes(gpg):
    b64 = gpg.split("\n")
    b64 = [x for x in b64 if x != ""]
    # Remove blank lines. Not strictly needed, but helpful
    x = 0
    while not(b64[x].startswith("-----BEGIN PGP MESSAGE-----")):
        x += 1
    start = x + 1
    while not(b64[x].startswith("-----END PGP MESSAGE-----")):
        x += 1
    finish = x - 1
    return base64.b64decode("".join(b64[start:finish]))


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
        print("    " + x)
    ids = "".join(known_ids).encode("ascii")

    lenids = int.to_bytes(len(known_ids), 2, "big")

    print("Going to send the length of the known IDS")
    print("As an integer: {}".format(len(known_ids)))
    print("As bytes: {}".format(lenids))
    print(lenids)

    s.send(lenids)

    print("Going to send following data to server")
    print(ids)

    s.sendall(ids)

    print("Known messages to the server sent")

    data = b""

    server_lenids_bytes = s.recv(2)
    server_lenids = int.from_bytes(server_lenids_bytes, "big")
    server_known_ids = []

    for _ in range(server_lenids):
        nextid = s.recv(64)
        print("got an ID, {}".format(nextid))
        server_known_ids.append(nextid.decode("ascii"))

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

    print("I need to send {} ID's to the server".format(len(tosend)))
    print("They are below")
    print()
    for x in tosend:
        print(x)

    for msg in tosend:
        tosend = known_messages[msg].serialise().encode("ascii")
        s.send(int.to_bytes(len(tosend), 8, "big"))
        s.sendall(tosend)

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
        newmsg = message(msg.decode("ascii"))
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

    for _ in range(client_lenids):
        nextid = conn.recv(64)
        print("got an ID, {}".format(nextid))
        client_known_ids.append(nextid.decode("ascii"))

    print("The client knows of {} messages, their ID's:".format(
        len(client_known_ids)))

    for x in client_known_ids:
        print("    " + x)

    # Now do it again, in reverse

    known_ids = [x for x in known_messages]
    print("I know of {} message, their ID's are below.".format(len(known_ids)))
    for x in known_ids:
        print("    " + x)

    lenids = len(known_ids)
    lenids_bytes = int.to_bytes(lenids, 2, "big")
    conn.send(lenids_bytes)

    tosend = "".join(known_ids).encode("ascii")
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
        newmsg = message(msg.decode("ascii"))
        print(newmsg)
        print("Adding new message object to the set of known messages")
        known_messages[newmsg.msgid] = newmsg

    print("Okay, I'm done recieving the client's messages!")

    print("I know of {} messages, they are below".format(len(known_messages)))
    for x in known_messages:
        print(known_messages[x])

    # Now I copy paste and hope for the best!

    for msg in tosend:
        tosend = known_messages[msg].serialise().encode("ascii")
        conn.send(int.to_bytes(len(tosend), 8, "big"))
        conn.sendall(tosend)

    print("Sync finished!")
    print()
    print()
    print()
    print()

for path in os.listdir("both"):
    with open("both/" + path) as f:
        m = convmsg(f.read())
        known_messages[m.msgid] = m

if sys.argv[1] == "SERVER":
    for path in os.listdir("server"):
        with open("server/" + path) as f:
            m = convmsg(f.read())
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
        with open("client/" + path) as f:
            m = convmsg(f.read())
            known_messages[m.msgid] = m

    sync("localhost")
    print()
    print("*"*60)
    print("==syncing AGAIN, should be a NOP==")
    print("*"*60)
    print()
    sync("localhost")
