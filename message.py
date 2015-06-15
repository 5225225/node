import config
import hashlib

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
                raise ValueError("Message ID does not match expected ID")
        if proof == -1:
            self.proof = mkproof(self.msgid)
        else:
            self.proof = proof

        self.gpg = gpg

        proofhash = hashlib.sha256(int.to_bytes(self.proof, 8, "big") + self.msgid).digest()
        if not proofhash.startswith(b"\x00"*config.POW_DIGITS):
            raise POWerror("Invalid proof when creating message")

    def __repr__(self):
        return "message {}:{}".format(
            hex(self.proof),
            hex(int.from_bytes(self.msgid, "big")))

