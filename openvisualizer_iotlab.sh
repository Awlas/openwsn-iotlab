#!/bin/bash
source $HOME/venv/bin/activate


cd "$(dirname "$0")"

#exp id if specified
if [ "$1" ]; then exp="-i $1"; fi

#get the list of nodes reserved so far
NODES=`iotlab-experiment get $exp -r | ./parse_json.py "
','.join(
[ node['network_address'].split('.')[0]
  for node in x['items']
]
)"
`


#construct the rgs and start OV
cd $HOME/openwsn-sw/software/openvisualizer/bin/openVisualizerApp
python openVisualizerWeb.py --port 1278  --iotlabmotes $NODES

