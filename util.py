import sys
import socket
import tempfile
import subprocess
import os
import message


def send_ids(sock, ids):
    idsjoined = b"".join(ids)
    lenids = int.to_bytes(len(ids), 2, "big")
    sock.send(lenids)
    sock.sendall(idsjoined)


def recv_ids(sock):
    ids = set()
    lenids = int.from_bytes(sock.recv(2), "big")
    for _ in range(lenids):
        nextid = sock.recv(32)
        ids.add(nextid)
    return ids


def send_msgs(sock, tosend, msgstore):
    for msgid in tosend:
        msg = msgstore[msgid].serialise()
        sock.send(int.to_bytes(len(msg), 8, "big"))
        sock.sendall(msg)


def recv_msgs(sock, amount):
    messages = []
    for _ in range(amount):
        data = b""
        msglen = int.from_bytes(sock.recv(8), "big")
        while len(data) < msglen:
            newdata = sock.recv(64)
            data += newdata
        newmsg = message.message.from_serialised(msg)
        messages.append(newmsg)

    return messages


def calc_needed(own, remote):
    own = set(own)
    remote = set(remote)
    return (own - remote, remote - own)


def getinput():
    messagef = tempfile.mkstemp()[1]
    subprocess.call(["/usr/bin/vim", messagef])
    msgf = open(messagef)
    data = msgf.read()
    msgf.close()
    os.unlink(messagef)
    return data


def writeoutput(data):
    messagef = tempfile.mkstemp()[1]
    msgf = open(messagef, "w")
    msgf.write(data)
    msgf.close()
    subprocess.call(["/usr/bin/vim", messagef])
    os.unlink(messagef)


def closesocket(s):
    # TODO find out why OSX complains about this
    try:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    except OSError:
        pass


def btostring(bytestring):
    return bytestring.replace(b"\x00", b"").decode("ascii")


def fromhex(hexstring, length):
    return int(hexstring, 16).to_bytes(length, "big")


def tohex(bytestring):
    x = str(hex(int.from_bytes(bytestring, "big")))[2:]
    x = x.rjust(64, "0")
    return "0x" + x


def vercheck():
    if sys.version_info.major < 3:
        print("This program requires python 3 to be used")
        print("You know, there's a reason why it's called a README.md")
        sys.exit(1)
