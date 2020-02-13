#!/bin/bash

#compiation & firmwares
FW_SRC_DAGROOT="../openwsn-fw-dagroot"
FW_SRC_DEVICE="../openwsn-fw-device"
FW_BIN="build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog"
FW_BIN_DAGROOT="../scripts/firmwares/03oos_openwsn_prog_dagroot"
FW_BIN_DEVICE="../scripts/firmwares/03oos_openwsn_prog_device"

#firmwares on iotlab
FW_BIN_DAGROOT_IOTLAB="A8/03oos_openwsn_prog_dagroot"
FW_BIN_DEVICE_IOTLAB="A8/03oos_openwsn_prog_device"

#parameters for experiments
USER=theoleyr
SITE=strasbourg
NAME="OVIZ"
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


echo "------- mirroring for devices vs DAGROOT firmwares ------"
rsync -av --delete-after --exclude '.sconsign.dblite' --exclude 'build' --exclude 'projects/common'  $FW_SRC_DEVICE/ $FW_SRC_DAGROOT

echo
echo
echo





echo "----- searching for an existing running experiment -------"
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

	echo "----- reserving one experiment -------"
	CMD="iotlab-experiment submit -n $NAME -d $DURATION -l $NBNODES,archi=$ARCHI:at86rf231+site=$SITE"
	echo $CMD
	RES=`$CMD`
	EXPID=`echo $RES | grep id | cut -d ":" -f 2 | cut -d "}" -f 1`
	echo "ExperimentId=$EXPID"
	echo
	echo
	echo

fi


#get the correct site
echo "----- Site Identification -------"
CMD="iotlab-experiment get -i $EXPID -r"
echo $CMD
$CMD > json.dump
SITE=`python site_get.py | cut -d "." -f 1 | cut -d "-" -f 2 `
echo $SITE
if [ -z "$SITE" ]
then
	exit 5
fi
#remove tmp file
rm json.dump



#wait the experiment starts runing
echo "----- waiting the experiment is in running mode -------"
iotlab-experiment wait -i $EXPID
echo
echo
echo


#EXperiment Identification
#get the list of nodes
CMD="iotlab-experiment get -i $EXPID -r"
#echo $CMD
$CMD > json.dump
NODES_LIST=`python nodes_list.py | cut -d "." -f 1 | cut -d "-" -f 2 ` 
echo "the site has been identified to $SITE"
#tmp file
rm json.dump
echo
echo
echo



#Compilation
echo "------- Compilation ------"

echo " Compiling dagroot..."
echo "Directory $FW_SRC_DAGROOT"
cd $FW_SRC_DAGROOT
CMD="scons board=$BOARD toolchain=armgcc dagroot=1 oos_openwsn"
echo $CMD
$CMD
#errors
if [ $? -ne 0 ]
then
echo "Compilation error (dagroot)"
exit 5
fi
echo "cp $FW_BIN $FW_BIN_DAGROOT"
cp $FW_BIN $FW_BIN_DAGROOT
CMD="scp $FW_BIN $USER@$SITE.iot-lab.info:$FW_BIN_DAGROOT_IOTLAB"
echo $CMD
$CMD

echo " Compiling devices..."
echo "Directory $FW_SRC_DEVICE"
cd $FW_SRC_DEVICE
CMD="scons board=$BOARD toolchain=armgcc dagroot=0 oos_openwsn"
echo $CMD
$CMD
#errors
if [ $? -ne 0 ]
then
echo "Compilation error (device)"
exit 6
fi
echo "cp $FW_BIN $FW_BIN_DEVICE"
cp $FW_BIN $FW_BIN_DEVICE
CMD="scp $FW_BIN $USER@$SITE.iot-lab.info:$FW_BIN_DEVICE_IOTLAB"
echo $CMD
$CMD



echo
echo
echo







#A8 boot
if [ "$ARCHI" == "a8" ]
then
    echo "------- Wait that a8 nodes boot ------"
    iotlab-ssh wait-for-boot
fi






#construct an array for the node
nbnodes=0
for N in $NODES_LIST
do
    NODES[$nbnodes]=$N
    ((nbnodes++))
done
echo "$nbnodes nodes"



#flash the dagroot
i=0
while [ $i -lt $nbnodes ]
do
    if [ $ARCHI == "m3" ]
    then
        CMD="iotlab-node --update $FW_BIN_DAGROOT -l $SITE,$ARCHI,${NODES[$i]} -i $EXPID"
    else
    #    CMD="iotlab-ssh  -i $EXPID flash-m3 $FW_BIN_DAGROOT -l $SITE,$ARCHI,${NODES[$i]}"
        CMD="iotlab-ssh -i $EXPID --verbose run-cmd \"flash_a8_m3 $FW_BIN_DAGROOT_IOTLAB\" -l $SITE,$ARCHI,${NODES[$i]}"
    fi
    echo "----- Flashing the dagroot -------"
    echo $CMD
    $CMD > $REP_CURRENT/json_flash.dump
    
    #error??
    REP=`pwd`
    cd $REP_CURRENT
    RESULT=`python cmd_result.py`
    ERROR=`echo $RESULT | grep ko`
    OK=`echo $RESULT | grep ok`
    cd $REP
    echo "$OK" | tr " " "\n"
    #tmp file
    rm $REP_CURRENT/json_flash.dump

    ##everything is ok
    if [ $? -eq 0 ] && [ -z "$ERROR" ]
    then
        port=10000
        SSHPORTS="-L $port:m3-${NODES[$i]}:20000"
        PORTS[0]=$port
        break
    fi

    ((i++))
done
echo
echo
echo


#flash the other motes

#first mote in the list
((i++))
if [ $ARCHI == "m3" ]
then
    CMD="iotlab-node --update $FW_BIN_DEVICE -i $EXPID -l $SITE,$ARCHI,${NODES[$i]}"
else
    CMD="iotlab-ssh -i $EXPID  flash-m3 $FW_BIN_DEVICE -l $SITE,$ARCHI,${NODES[$i]}"
    CMD="iotlab-ssh -i $EXPID --verbose run-cmd \"flash_a8_m3 $FW_BIN_DEVICE_IOTLAB\" -l $SITE,$ARCHI,${NODES[$i]}"
fi
((port++))
SSHPORTS="$SSHPORTS -L $port:m3-${NODES[$i]}:20000"
PORTS[${#PORTS[@]}]=$port
((i++))

#remaining nodes (with a + to concatenate the command)"
while [ $i -lt $nbnodes ]
do
    CMD="$CMD+${NODES[$i]}"
    ((port++))
    SSHPORTS="$SSHPORTS -L $port:m3-${NODES[$i]}:20000"
    PORTS[${#PORTS[@]}]=$port
    ((i++))
done
echo "----- Flashing the devices -------"
echo $CMD
$CMD > $REP_CURRENT/json_flash.dump


#error??
REP=`pwd`
cd $REP_CURRENT
RESULT=`python cmd_result.py`
ERROR=`echo $RESULT | grep ko`
OK=`echo $RESULT | grep ok`
cd $REP
echo "$OK" | tr " " "\n"
#tmp file
rm $REP_CURRENT/json_flash.dump


echo
echo




#ssh forwarding
echo "----- Forwarding the serial ports (ssh)  -------"
CMD="killall ssh"
echo $CMD
$CMD
echo $?
CMD="ssh -fN $USER@$SITE.iot-lab.info $SSHPORTS"
echo $CMD
$CMD
echo
echo
echo

#Scat TUNNELING
echo "----- SOCAT TUNNELING ------"
sudo killall socat
sleep 1;
i=0
for port in "${PORTS[@]}"
do
    echo "tcpPort $port -> /dev/ttyUSB"$i
    echo "sudo socat PTY,raw,echo=0,link=/dev/ttyUSB"$i" tcp:127.0.0.1:$port"
    sudo socat PTY,raw,echo=0,link=/dev/ttyUSB"$i" tcp:127.0.0.1:$port &
    ((i++))
done

echo
echo
echo


#end
#iotlab-experiment stop -i $EXPID
