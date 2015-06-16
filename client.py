import config
import message
import socket
import tempfile
import subprocess
import os

known_messages = {}
my_messages = set()
# To avoid duplication, my_messages is simply a set of message ID's

def tohex(bytestring):
    return str(hex(int.from_bytes(bytestring, "big")))
    

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
print("inserting test message at client/test")
x = message.message(f.read())
known_messages[x.msgid] = x
first_help = True
while True:
    print()
    x = input("> ").split(" ")
    command, arguments = x[0], x[1:]
    if command == "sync":
        if len(arguments) == 2:
            sync(arguments[0], int(arguments[1]))
        elif len(arguments) == 1:
            sync(arguments[0])
        elif len(arguments) == 0:
            sync("localhost")

    elif command == "ls":
        for msgid in known_messages:
            print(tohex(msgid))

    elif command == "help" and len(arguments) == 0:
        if first_help:
            print("Square brackets indicate optional arguments")
            print("A default is given for some commands")
            print("")
            first_help = False
        print("sync [IP = localhost] [PORT = 3514]")
        print("ls")
        print("help")

    elif command == "msg":
        messagef = tempfile.mkstemp()[1]
        subprocess.call(["/usr/bin/vim", messagef])
        msgf = open(messagef)
        data = msgf.read()
        msgf.close()
        os.unlink(messagef)

        encsign = subprocess.check_output(
            ["gpg", "--encrypt", "--sign"],
            input=data.encode("UTF-8"),
        )

        newmsg = message.message(encsign)
        known_messages[newmsg.msgid] = newmsg
        print("ID: {}".format(tohex(newmsg.msgid)))
        print("Message added to known messages")
        print("Run a sync against a known node, or wait for the syncd to run")

    elif command == "read":
        if len(arguments) == 0:
            print("What do you want me to read?")
        else:
            foundmsgs = []
            wantedhex = arguments[0]
            if not(wantedhex.startswith("0x")):
                wantedhex = "0x" + wantedhex
            wantedhex = wantedhex.encode("ascii")

            for msgid in known_messages:
                msgidhex = tohex(msgid)
                if msgidhex.startswith(wantedhex.decode("ascii")):
                    foundmsgs.append(msgid)

            if len(foundmsgs) > 1:
                print("More than one message found, be more specific")
            elif len(foundmsgs) == 0:
                print("No messages found")
            else:
                msg = known_messages[foundmsgs[0]].gpg
                decrypted = subprocess.check_output("gpg", input=msg,
                stderr=subprocess.DEVNULL).decode("UTF-8")
                print(decrypted)

    else:
        print("Unknown command")
