import config
import message
import socket
import tempfile
import subprocess
import os
import util
import sys

util.vercheck()

known_messages = message.messagestore(config.MSGDIR)

def discover_hosts(port=config.BROADPORT):
    known_addrs = []

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(b"PING", ("255.255.255.255", port))
    s.settimeout(2)
    while True:
        try:
            data, addr = s.recvfrom(4)
            if data == b"PONG":
                known_addrs.append(addr[0])
        except socket.timeout:
            break
    return known_addrs

def sync(ip, port=3514):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Connecting to {}:{}".format(ip, port))
    s.connect((ip, port))
    s.send(config.PROTOCOL_VERSION)
    serverver = s.recv(16)
    print("Connected to server")
    print("Server version: {}".format(util.btostring(serverver)))
    print("Client version: {}".format(util.btostring(config.PROTOCOL_VERSION)))

    if serverver != config.PROTOCOL_VERSION:
        print("Hold on, that's not the right version... Disconnect!")
        util.closesocket(s)
        return

    known_ids = [x for x in known_messages.keys()]
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
        util.closesocket(s)
        return

    for msg in tosend:
        msg = known_messages[msg].serialise()
        s.send(int.to_bytes(len(msg), 8, "big"))
        s.sendall(msg)

    for _ in range(len(torecv)):
        msglen = int.from_bytes(s.recv(8), "big")
        msg = s.recv(msglen)
        newmsg = message.message.from_serialised(msg)
        known_messages[newmsg.msgid] = newmsg

    print("Synced Sucessfully")
    print("Sent the server {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))

