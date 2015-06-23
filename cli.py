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
            print("Angle brackets indicate required arguments")
            print("A default is given for some commands")
            print("")
            first_help = False
        print("sync [IP = localhost] [PORT = 3514]")
        print("ls")
        print("help [COMMAND]")
        print("msg [recipients]")
        print("attach [recipients] <filename>")
        print("read <msgid>")
    elif command == "help" and len(arguments) > 0:
        helpcmd = arguments[0]

        if helpcmd == "sync":
            print("Push and pull all your currently known messages to the")
            print("specified server. With no arguments, sync with own daemon")
            print("which won't do anything, but is good for debugging.")

        elif helpcmd == "ls":
            print("List all known messages by their msgid. Does not filter")
            print("for if you can actually read them at the moment")

        elif helpcmd == "help":
            print("You're using it now.")

        elif helpcmd == "attach":
            print("Allows you to insert binary files to the network.")
            print("Currently there are no restrictions, but obviously")
            print("inserting a 4GB file will be slow, and in the future")
            print("nodes may reject large files, or delete them sooner.")

        elif helpcmd == "read":
            print("Read the message specified by the msgid.")
            print("Partial ids are supported, with/without the 0x prefix.")

        elif helpcmd == "msg":
            print("Write textual messages in an editor")

    elif command == "msg":
        recipients = arguments
        if len(recipients) == 0:
            print("Enter email addresses one by one for recipients")
            print("These must be the same as GPG knows them as")
            print("The above is very important, you might want to run")
            print("    gpg --list-keys")
            print("To make sure you're using the correct email")
            print("There is currently no error checking for invalid input")
            print()
            print("Enter a blank line to end input")
            while True:
                r = input("email: ")
                if r == "":
                    break
                recipients.append(r.strip())

        data = util.getinput()
        program = ["gpg", "--encrypt", "--sign"]
        for r in recipients:
            program.append("-r")
            program.append(r)
        encsign = subprocess.check_output(program, input=data.encode("UTF-8"))

        newmsg = message.message(encsign)
        known_messages[newmsg.msgid] = newmsg
        print("ID: {}".format(util.tohex(newmsg.msgid)))
        print("Message added to known messages")
        print("Run a sync against a known node, or wait for the syncd to run")

    elif command == "attach":
        recipients = arguments[:-1]
        fname = arguments[-1]
        with open(fname, "rb") as f:
            data = f.read()
        program = ["gpg", "--encrypt", "--sign"]
        for r in recipients:
            program.append("-r")
            program.append(r)
        encsign = subprocess.check_output(program, input=data)
        newmsg = message.message(encsign)
        known_messages[newmsg.msgid] = newmsg
        print("ID: {}".format(util.tohex(newmsg.msgid)))
        print("Attachment added to known messages")
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
                                                    )
                try:
                    decrypted = decrypted.decode("UTF-8")
                    util.writeoutput(decrypted)
                except UnicodeDecodeError:
                    # Likely a binary file.
                    print("The file can't be decoded, likely an attachment.")
                    print("Enter a filename to save it as")
                    fname = input("fname: ")
                    with open(fname, "wb") as f:
                        f.write(decrypted)

    else:
        print("Unknown command")
