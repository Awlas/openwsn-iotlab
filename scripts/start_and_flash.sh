#!/bin/bash

#parameters
DURATION=65
FW_SRC_DAGROOT=/home/theoleyre/openwsn/openwsn-fw-dagroot
FW_SRC_DEVICE=/home/theoleyre/openwsn/openwsn-fw-device
FW_BIN=build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog
FW_BIN_DAGROOT=/home/theoleyre/openwsn/scripts/firmwares/03oos_openwsn_prog_dagroot
FW_BIN_DEVICE=/home/theoleyre/openwsn/scripts/firmwares/03oos_openwsn_prog_device
NBNODES=4
USER=theoleyr
SITE=strasbourg
ARCHI=m3
NAME="OVIZ"

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

	#wait it starts runing
	echo "----- waiting the experiment is in running mode -------"
	iotlab-experiment wait -i $EXPID
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


#EXperiment Identification
#get the list of nodes
CMD="iotlab-experiment get -i $EXPID -r"
#echo $CMD
$CMD > json.dump
NODES_LIST=`python nodes_list.py | cut -d "." -f 1 | cut -d "-" -f 2 ` 
echo "the site has been identified to $SITE"
echo
echo
echo



#Compilation
echo "------- Compilation ------"

echo " Compiling dagroot..."
echo "Directory $FW_SRC_DAGROOT"
cd $FW_SRC_DAGROOT
echo "scons board=iot-lab_M3 toolchain=armgcc dagroot=1 oos_openwsn"
scons board=iot-lab_M3 toolchain=armgcc dagroot=1 oos_openwsn
#errors
if [ $? -ne 0 ]
then
echo "Compilation error (dagroot)"
exit 5
fi
echo "cp $FW_BIN $FW_BIN_DAGROOT"
cp $FW_BIN $FW_BIN_DAGROOT



echo " Compiling devices..."
echo "Directory $FW_SRC_DEVICE"
cd $FW_SRC_DEVICE
echo "scons board=iot-lab_M3 toolchain=armgcc dagroot=0 oos_openwsn"
scons board=iot-lab_M3 toolchain=armgcc dagroot=0 oos_openwsn
#errors
if [ $? -ne 0 ]
then
echo "Compilation error (device)"
exit 6
fi
echo "cp $FW_BIN $FW_BIN_DEVICE"
cp $FW_BIN $FW_BIN_DEVICE



echo
echo
echo





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
	CMD="iotlab-node --update $FW_BIN_DAGROOT -l $SITE,$ARCHI,${NODES[$i]} -i $EXPID"
	echo "----- Flashing the dagroot -------"
	echo $CMD
	$CMD

	##everything is ok
	if [ $? -eq 0 ]
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
CMD="iotlab-node --update $FW_BIN_DEVICE -i $EXPID -l $SITE,$ARCHI,${NODES[$i]}"
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
$CMD
echo
echo
echo




#ssh forwarding
echo "----- Forwarding the serial ports (ssh)  -------"
killall ssh
CMD="ssh -fN $USER@$SITE.iot-lab.info $SSHPORTS"
echo $CMD
$CMD
echo
echo
echo

#Scat TUNNELING
echo "----- SOCAT TUNNELING ------"
echo $SOCAT
#SOCAT=$SOCAT" sudo socat PTY,raw,echo=0,link=/dev/ttyUSB"$i" tcp:127.0.0.1:$port,fork;"
#$SOCAT
i=0
sudo killall socat
sleep 1;
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
