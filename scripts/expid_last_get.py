# parses JSON reply, and identifies the experiment id 

import json

with open("json.dump", "r") as readfile:
    infos=json.load(readfile)

#pick the last (most recent) experiment
print(infos["Running"][-1])

