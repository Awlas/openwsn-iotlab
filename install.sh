#!/bin/bash

REPO_FW=https://github.com/openwsn-berkeley/openwsn-fw.git
REPO_SW=https://github.com/openwsn-berkeley/openwsn-sw.git

# Current repository
REP=`pwd`

# Firmware
echo "------------------------"
echo "Clonning Firmwares"
cd $REP
sudo rm -Rf openwsn-fw-dagroot
sudo git clone $REPO_FW
mv openwsn-fw openwsn-fw-dagroot
sudo rm -Rf openwsn-fw-device
sudo cp -Rf openwsn-fw-dagroot openwsn-fw-device

# Software tools
echo "------------------------"
echo "Cloning openwsn-sw tools"
cd $REP
sudo rm -Rf openwsn-sw
sudo git clone $REPO_SW

# CoAP
echo "------------------------"
echo "Installing CoAP option"
cd $REP
sudo rm -rf coap
sudo git clone https://github.com/openwsn-berkeley/coap.git

#Install Cli Tools
echo "------------------------"
echo "Installing cli-tools"
sudo rm -Rf cli-tools
sudo git clone https://github.com/iot-lab/cli-tools.git

