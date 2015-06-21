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

    util.send_ids(s, known_messages.keys())
    server_known_ids = util.recv_ids(s)

    client_ids = set(known_messages.keys())
    server_ids = set(server_known_ids)

    client_ignored_ids = known_messages.ignored
    util.send_ids(s, client_ignored_ids)

    server_ignored_ids = util.recv_ids(s)

    tosend, torecv = util.calc_needed(client_ids, server_ids)

    tosend = tosend - server_ignored_ids
    torecv = torecv - client_ignored_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        util.closesocket(s)
        return

    util.send_msgs(s, tosend, known_messages)

    for msg in util.recv_msgs(s, len(torecv)):
        known_messages[msg.msgid] = msg

    print("Synced Sucessfully")
    print("Sent the server {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))
