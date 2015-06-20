import config
import message
import socket
import client
import random
import time

hosts = []

if config.CREATE_BROADCASTS:
    print("Going to try to discover LAN hosts")
    for host in client.discover_hosts():
        hosts.append(host)
else:
    print("Not going to try to discover LAN hosts.")
    print("If you want to enable this, set CREATE_BROADCASTS in config.py")

with open("known_hosts") as f:
    for host in f.readlines():
        hosts.append(host.strip())

while True:
    random.shuffle(hosts)
    for item in hosts:
        print(item)
        try:
            client.sync(item)
        except OSError:
            print("{} doesn't seem to be running anymore".format(item))
            print("deleting it")
            del hosts[item]
        time.sleep(240*random.uniform(5, 1.5))
