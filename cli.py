import client
import message
import config
import util
import tempfile
import subprocess
import os

known_messages = message.messagestore(config.MSGDIR)

first_help = True
while True:
    print()
    x = input("> ").split(" ")
    command, arguments = x[0], x[1:]
    if command == "sync":
        if len(arguments) == 2:
            client.sync(arguments[0], int(arguments[1]))
        elif len(arguments) == 1:
            client.sync(arguments[0])
        elif len(arguments) == 0:
            client.sync("localhost")

    elif command == "ls":
        for msgid in known_messages.keys():
            print(util.tohex(msgid))

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
        print("ID: {}".format(util.tohex(newmsg.msgid)))
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

            for msgid in known_messages.keys():
                msgidhex = util.tohex(msgid)
                if msgidhex.startswith(wantedhex.decode("ascii")):
                    foundmsgs.append(msgid)

            if len(foundmsgs) > 1:
                print("More than one message found, be more specific")
            elif len(foundmsgs) == 0:
                print("No messages found")
            else:
                msg = known_messages[foundmsgs[0]].gpg
                decrypted = subprocess.check_output("gpg",
                                                    input=msg,
                                                    stderr=subprocess.DEVNULL
                                                    ).decode("UTF-8")
                print(decrypted)

    else:
        print("Unknown command")
