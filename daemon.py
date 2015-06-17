import socket
import message
import config
import util

util.vercheck()

known_messages = {}


def listen(socket):
    conn, addr = s.accept()
    clientver = conn.recv(16)
    print("{} connected".format(addr))
    print("Server version: {}".format(util.btostring(config.PROTOCOL_VERSION)))
    print("Client version: {}".format(util.btostring(clientver)))

    if clientver != config.PROTOCOL_VERSION:
        print("Disconnecting {} due to mismatching versions".format(addr))
        conn.send(config.PROTOCOL_VERSION)
        conn.close()
        return

    conn.send(config.PROTOCOL_VERSION)

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
        newmsg = message.message.from_serialised(msg)
        known_messages[newmsg.msgid] = newmsg

    # Now I copy paste and hope for the best!

    for msg in tosend:
        send = known_messages[msg].serialise()
        conn.send(int.to_bytes(len(send), 8, "big"))
        conn.sendall(send)

    print("Synced sucessfuly")
    print("Sent the client {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))
    print()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", config.PORT))
s.listen(5)
print("Ready!")
while True:
    listen(s)
