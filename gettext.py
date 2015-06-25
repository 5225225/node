import sys
import tty
import termios
import os
import keycodes


def rmchar(bytestr, index):
    start = bytestr[:index]
    end = bytestr[index+1:]
    return start + end


def redraw(prompt, string):
    outwrite(b"\x1b[s", flush=False)
    outwrite(b"\x1b[2K\x1b[1G", flush=False)
    outwrite(prompt, flush=False)
    outwrite(string, flush=False)
    outwrite(b"\x1b[u", flush=False)


def log(x):
    with open("/tmp/outlog", "a") as f:
        f.write("-----\n")
        f.write(x.decode("ascii"))
        f.write("-----\n")


def isint(char):
    try:
        x = int(char)
        return True
    except:
        return False


def parsespecial():
    sequence = b"\x1b"
    sequence += readchar()
    log(sequence)
    if sequence[-1:] == b"[":
        sequence += readchar()
        log(sequence)
        if isint(sequence[-1:]):
            sequence += readchar()
            if isint(sequence[-1:]):
                # Is an F key
                sequence += readchar()
                return keycodes.lookup[sequence]
        elif sequence[-1:] in (b"A", b"B", b"C", b"D"):
            # Is an arrow key.
            return keycodes.lookup[sequence]


def outwrite(bytestr, flush=True):
    sys.stdout.buffer.write(bytestr)
    if flush:
        sys.stdout.flush()


def cursor():
    outwrite(b"\x1b[6n")
    response = b""
    while True:
        ch = readchar()
        if ch == b"R":
            break
        response += ch
    row, col = response[2:].split(b";")
    return int(col)


def readchar():
    x = sys.stdin.buffer.read(1)
    return x


def gettext(prompt):
    string = b""
    old = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin)

    if type(prompt) == str:
        prompt = prompt.encode("ascii")

    outwrite(prompt)
    while True:
        ch = readchar()
        if ch == b"\r":
            break
        elif ch == b"\x7f":
            if string != []:
                string = rmchar(string, cursor()-2-len(prompt))
                redraw(prompt, string)
                outwrite(b"\x1b[D")

        elif ch == b"\x1b":
            seq = parsespecial()
            if seq in ("RIGHT", "LEFT"):
                if seq == "RIGHT":
                    if not (cursor() > len(string) + len(prompt)):
                        outwrite(b"\x1b[C")
                else:
                    if not (cursor() <= len(prompt)+1):
                        outwrite(b"\x1b[D")
        elif ch[0] in range(0x01, 0x1b):
            char = keycodes.lookup[ch]
            if char == "^C":
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
                outwrite(b"\n")
            else:
                print(char)
        else:
            begin = string[:cursor()-1-len(prompt)]
            end = string[cursor()-1-len(prompt):]
            string = begin + ch + end
            redraw(prompt, string)
            outwrite(b"\x1b[C")
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
    outwrite(b"\n")
    return string.decode("ascii")
