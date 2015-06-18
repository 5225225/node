import config
import message
import socket

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
    print(known_addrs)
    return known_addrs

known_messages = message.messagestore(config.MSGDIR)
discover_hosts()
