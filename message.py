import config
import hashlib
import os
import util
import time


class POWerror(Exception):
    pass


def mkproof(msgid):
    proof = 0
    while True:
        if hashlib.sha256(
                    int.to_bytes(proof, 8, "big") +
                    msgid
                ).digest().startswith(b"\x00"*config.POW_DIGITS):
            break
        proof += 1
    return proof


class messagestore():

    def __getitem__(self, key):
        itempath = self.path + util.tohex(key)
        with open(itempath, "rb") as f:
            data = f.read()
        return message.from_serialised(data)

    def __setitem__(self, key, value):
        itempath = self.path + util.tohex(key)
        with open(itempath, "wb") as f:
            f.write(value.serialise())

    def keys(self):
        paths = list(os.listdir(self.path))
        bytepaths = []
        for item in paths:
            try:
                bytepaths.append(util.fromhex(item, 32))
            except ValueError:
                pass
                # Likely not a real key, ignore it.
        return bytepaths

    def ignorekey(self, key):
        with open("ignored-keys", "ab") as f:
            f.write(key)
        fname = util.tohex(key)
        if config.PRUNE_DELETE:
            os.remove(self.path + fname)
        else:
            os.rename(self.path + fname, self.path + "archive/" + fname)

    def prune(self):
        for msgid in self.keys():
            ctime = os.stat(self.path + util.tohex(msgid)).st_ctime
            diff = time.time() - ctime
            if diff > config.PRUNE_TIME:
                self.ignorekey(msgid)
                print("{} is too old, ignoring".format(util.tohex(msgid)))

    def __init__(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        self.path = path
        if not(self.path.endswith("/")):
            self.path = self.path + "/"
        self.ignored = []
        with open("ignored-keys", "rb") as f:
            while True:
                msgid = f.read(32)
                if not msgid:
                    break
                self.ignored.append(msgid)


class message:

    def from_serialised(sbytes):
        msgid = sbytes[:32]
        proof = sbytes[32:40]
        gpg = sbytes[40:]

        return message(gpg, int.from_bytes(proof, "big"), msgid)

    def serialise(self):
        x = bytes()

        x += self.msgid
        x += int.to_bytes(self.proof, 8, "big")
        x += self.gpg

        return x

    def __init__(self, gpg, proof=-1, msgid=""):
        if msgid == "":
            self.msgid = hashlib.sha256(gpg).digest()
        else:
            self.msgid = msgid
            expectedmsgid = hashlib.sha256(gpg).digest()
            if not(self.msgid == expectedmsgid):
                print("Given MSGID: {}".format(self.msgid))
                print("Expected MSGID: {}".format(expectedmsgid))
                raise ValueError("Message ID does not match expected ID")
        if proof == -1:
            self.proof = mkproof(self.msgid)
        else:
            self.proof = proof

        self.gpg = gpg

        proofhash = hashlib.sha256(
            int.to_bytes(self.proof, 8, "big") +
            self.msgid).digest()
        if not proofhash.startswith(b"\x00"*config.POW_DIGITS):
            raise POWerror("Invalid proof when creating message")

    def __repr__(self):
        return "message {}:{}".format(
            hex(self.proof),
            hex(int.from_bytes(self.msgid, "big")))
