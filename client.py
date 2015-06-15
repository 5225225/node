import config
import message
import socket

known_messages = {}

def sync(ip, port=3514):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Connecting to {}:{}".format(ip, port))
    s.connect((ip, port))
    s.send(config.PROTOCOL_VERSION)
    serverver = s.recv(16)
    print("Connected to server")
    print("Server version: {}".format(serverver.replace(b"\x00", b"").decode("ascii")))
    print("Client version: {}".format(config.PROTOCOL_VERSION.replace(b"\x00", b"").decode("ascii")))

    if serverver != config.PROTOCOL_VERSION:
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
        newmsg = message.message.from_serialised(msg)
        known_messages[newmsg.msgid] = newmsg

    print("Synced Sucessfully")
    print("Sent the server {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))

f = open("client/test", "rb")
x = message.message(f.read())
known_messages[x.msgid] = x

while True:
    sync("localhost", config.PORT)
    input()

