# parses JSON reply, and identifies the experiment id 

import json

with open("json_flash.dump", "r") as readfile:
    infos=json.load(readfile)


#pick the result for each name in the list
if "0" in infos:
    for info in infos["0"]:
        print("{0}: ok".format(info))

if "1" in infos:
    for info in infos["1"]:
        print("{0}: ko".format(info))
