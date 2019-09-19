#!/bin/bash

REPO_FW=https://github.com/ftheoleyre/openwsn-fw.git
REPO_SW=https://github.com/ftheoleyre/openvisualizer.git

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
echo "-------------------------------"
echo "Cloning openvisualizer tools"
cd $REP
sudo rm -Rf openvisualizer
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
sudo python setup.py install

# Packages
echo "------------------------"
echo "Installing Python packages"
cd $REP
cd openvisualizer
python -r requirements.txt
cd $REP
sudo rm -rf paho.mqtt.python
sudo git clone https://github.com/eclipse/paho.mqtt.python
cd paho.mqtt.python
sudo python setup.py install


