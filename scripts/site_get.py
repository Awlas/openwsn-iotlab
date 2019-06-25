# parses a json reply to identify the site where an experiment is currently running

import json

with open("json.dump", "r") as readfile:
    infos=json.load(readfile)

print infos["items"][0]["site"]
    

