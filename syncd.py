import config
import message
import socket
import client
import random

lan_hosts = {}
wan_hosts = {}

if config.CREATE_BROADCASTS:
    print("Going to try to discover LAN hosts")
    lan_hosts = client.discover_hosts()
    print("I found {} hosts".format(len(lan_hosts)))
    print("Printing them below")
    for host in lan_hosts:
        print(host)
else:
    print("Not going to try to discover LAN hosts.")
    print("If you want to enable this, set CREATE_BROADCASTS in config.py")
