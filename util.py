def btostring(bytestring):
    return bytestring.replace(b"\x00", b"").decode("ascii")


def tohex(bytestring):
    return str(hex(int.from_bytes(bytestring, "big")))
