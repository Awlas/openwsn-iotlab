#list the nodes from a JSON and translate them into a list of net addresses

import json

with open("json.dump", "r") as readfile:
    nodes=json.load(readfile)
#print(nodes)

#pick the network address
for node in nodes["items"]:
    print(node["network_address"])
