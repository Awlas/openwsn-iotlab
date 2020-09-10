#!/bin/bash

#compiation & firmwares
FW_SRC="../openwsn-fw"
FW_BIN="build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog"
FW_BIN_IOTLAB="A8/03oos_openwsn_prog"

#parameters for experiments
USER=theoleyr
SITE=lille
NAME="owsn"
NBNODES=4
DURATION=65

#architecture
#ARCHI="a8"
ARCHI="m3"
#BOARD="iot-lab_A8-M3"
BOARD="iot-lab_M3"



REP_CURRENT=`pwd`

echo
echo
echo


# Check if we're root and re-execute if we're not.
#[ `whoami` = root ] || { sudo "$0" "$@"; exit $?; }




echo "----- search for an existing running experiment -------"
CMD="iotlab-experiment get -e"
$CMD > json.dump 2> /dev/null
#cat json.dump
EXPID=`python expid_last_get.py 2> /dev/null | cut -d "." -f 1 | cut -d "-" -f 2 `
if [ - ]
then
	echo "We found the experiment id: '$EXPID'"
else
	echo "No already experiment running"
fi
#remove tmp file
rm json.dump
echo
echo
echo

if [ -z	"$EXPID" ]
then

	echo "----- reserve one experiment -------"
	CMD="iotlab-experiment submit -n $NAME -d $DURATION -l $NBNODES,archi=$ARCHI:at86rf231+site=$SITE"
	echo $CMD
	RES=`$CMD`
	EXPID=`echo $RES | grep id | cut -d ":" -f 2 | cut -d "}" -f 1`
	echo "ExperimentId=$EXPID"
	echo
	echo
	echo

fi



#wait the experiment starts runing
echo "----- wait that the experiment is in running mode -------"
iotlab-experiment wait -i $EXPID
echo
echo
echo


#get the correct site
echo "----- Site Identification -------"
CMD="iotlab-experiment get -i $EXPID -n"
echo $CMD
$CMD > json.dump
SITE=`python site_get.py | cut -d "." -f 1 | cut -d "-" -f 2 `
echo $SITE
if [ -z "$SITE" ]
then
	exit 5
fi
echo
echo
echo


#EXperiment Identification
#get the list of nodes
echo "----- Nodes Identification -------"
NODES_LIST=`python nodes_list.py | cut -d "." -f 1 | cut -d "-" -f 2 `
echo "the nodes have been identified to"
echo "$NODES_LIST"
#tmp file
rm json.dump
echo
echo
echo


#transform the list of nodes in an array
nbnodes=0
for N in $NODES_LIST
do
    NODES[$nbnodes]=$N
    ((nbnodes++))
done
echo "$nbnodes nodes"





#Compilation
echo "------- Compilation ------"


echo " Compiling firmware..."
echo "Directory $FW_SRC"
cd $FW_SRC
CMD="scons board=$BOARD toolchain=armgcc boardopt=printf modules=coap,udp apps=cjoin,cexample oos_openwsn"
echo $CMD
$CMD
#errors
if [ $? -ne 0 ]
then
echo "Compilation error (device)"
exit 6
fi



echo
echo
echo




#A8 boot
if [ "$ARCHI" == "a8" ]
then
    echo "------- Wait that a8 nodes boot ------"
    iotlab-ssh wait-for-boot
fi





#Compilation
echo "------- Flash the devices ------"





#flash the motes
i=0
port=10000

if [ $ARCHI == "m3" ]
then
    CMD="iotlab-node --flash $FW_BIN -i $EXPID"
    #by default, all the nodes, no need to specify the exhaustive list
    #NB: same firmware for all the nodes. One will be slected at runtime as dagroot
    #-l $SITE,$ARCHI,${NODES[$i]}"
else
    CMD="iotlab-ssh -i $EXPID --verbose run-cmd \"flash_a8_m3 $FW_BIN_IOTLAB\"
    echo "be careful, not tested with the novel cli tools, remove the next "exit()" to test it"
    exit
    #-l $SITE,$ARCHI,${NODES[$i]}"
fi


#flash command
echo $CMD
$CMD > $REP_CURRENT/json_flash.dump

    
    

#parse the results for the flash command
REP=`pwd`
cd $REP_CURRENT
RESULT=`python cmd_result.py`
ERROR=`echo $RESULT | grep ko`
OK=`echo $RESULT | grep ok`
cd $REP
echo "$OK" | tr " " "\n"
#tmp file
cat $REP_CURRENT/json_flash.dump
rm $REP_CURRENT/json_flash.dump
echo
echo






# OpenViz server
echo "----- OpenVisualizer ------"
cd $REP_CURRENT
cd ../openvisualizer

echo "install the current version of Openvisualizer"
CMD="pip install -e ."
echo $CMD
$CMD > /dev/null

#with opentun and -d for wireshark debug
echo ""
echo "starst Openvisualizer (server part)"
CMD="openv-server --opentun --mqtt-broker 127.0.0.1 -d --fw-path /home/theoleyre/openwsn/openwsn-fw --iotlab-motes "
MAX=`expr $nbnodes - 1`
for i in `seq 0 $MAX`;
do
        CMD="$CMD $ARCHI-${NODES[$i]}.$SITE.iot-lab.info"
done
#run in background
CMD="$CMD"
echo $CMD
$CMD &
PID_OPENVSERVER=$!
echo "PID of openv-server to kill when the program exits: $PID_OPENVSERVER"


#let the server start
while [ -n "`openv-client motes | grep refused`" ]
do
    sleep 1
    echo "openv-server not yet started"
done







# OpenViz client
echo "----- Force the reboot of the motes ------"
CMD="iotlab-node --reset -i $EXPID"
echo $CMD
$CMD

echo "----- Config after boot ------"
# dagroot selection -> first mote (last 4 digits of the MAC address"
echo "openv-client motes | grep Ok | head -n 1 | cut -d '|' -f 3"
RES=`openv-client motes | grep Ok | head -n 1 | cut -d '|' -f 3`
echo "setting mote '$RES' as dagroot"
CMD="openv-client root $RES"
echo $CMD
$CMD



#web interface
openv-client view web




# kill the server part
echo "----- Stops openv-server ------"
echo "kill openv-server (pid=$PID_OPENVSERVER)"
CMD="kill -SIGKILL $PID_OPENVSERVER"
echo $CMD
$CMD







#end
#iotlab-experiment stop -i $EXPID

