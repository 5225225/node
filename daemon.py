import socket
import message
import config
import util
import threading

util.vercheck()

known_messages = message.messagestore(config.MSGDIR)
known_messages.prune()


class broadcast_listen(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.port = config.BROADPORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.port))
        while True:
            data, addr = self.sock.recvfrom(4)
            if data == b"PING":
                self.sock.sendto(b"PONG", addr)


def listen(socket):
    conn, addr = s.accept()
    clientver = conn.recv(16)
    print("{} connected".format(addr))
    print("Server version: {}".format(util.btostring(config.PROTOCOL_VERSION)))
    try:
        print("Client version: {}".format(util.btostring(clientver)))
    except UnicodeDecodeError:
        print("Non-ascii client version, disconnect now.")
        conn.send(config.PROTOCOL_VERSION)
        util.closesocket(conn)
        return

    if clientver != config.PROTOCOL_VERSION:
        print("Disconnecting {} due to mismatching versions".format(addr))
        conn.send(config.PROTOCOL_VERSION)
        util.closesocket(conn)
        return

    conn.send(config.PROTOCOL_VERSION)

    client_known_ids = util.recv_ids(conn)
    util.send_ids(conn, known_messages.keys())

    server_ids = set(known_messages.keys())
    client_ids = set(client_known_ids)

    tosend, torecv = util.calc_needed(server_ids, client_ids)

    client_ignored_ids = util.recv_ids(conn)

    server_ignored_ids = known_messages.ignored
    util.send_ids(conn, server_ignored_ids)

    tosend = tosend - client_ignored_ids
    torecv = torecv - server_ignored_ids

    if len(tosend) == 0 and len(torecv) == 0:
        print("Actually, I have nothing to do! Shutting down")
        util.closesocket(conn)
        return

    recvmsgs = []
    try:
        recvmsgs = util.recv_msgs(conn, len(torecv))
    except ValueError:
        print("*WARNING*")
        print("Message ID mismatch.")
        print("This could be a corrupted file, a bug, or intentional")
        print("Don't trust this client. Still, send your own messages")

        util.send_msgs(conn, tosend, known_messages)
        return 1

    for msg in recvmsgs:
        known_messages[msg.msgid] = msg

    util.send_msgs(conn, tosend, known_messages)

    print("Synced sucessfuly")
    print("Sent the client {} messages".format(len(tosend)))
    print("Got sent {} messages".format(len(torecv)))
    print()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", config.PORT))
s.listen(5)
print("Ready!")
print("I know of {} keys".format(len(known_messages.keys())))

if config.LISTEN_FOR_BROADCASTS:
    broadcast_listen().start()
while True:
    listen(s)
