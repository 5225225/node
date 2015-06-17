import sys
import socket


def closesocket(s):
    # TODO find out why OSX complains about this
    try:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    except OSError:
        pass


def btostring(bytestring):
    return bytestring.replace(b"\x00", b"").decode("ascii")


def tohex(bytestring):
    return str(hex(int.from_bytes(bytestring, "big")))


def vercheck():
    if sys.version_info.major < 3:
        print("This program requires python 3 to be used")
        print("You know, there's a reason why it's called a README.md")
        sys.exit(1)
