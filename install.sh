#!/bin/bash

REPO_FW=https://github.com/ftheoleyre/openwsn-fw.git
REPO_SW=https://github.com/ftheoleyre/openvisualizer.git

# Current repository
REP=`pwd`

# Firmware
echo "------------------------"
echo "Clonning Firmwares"
cd $REP
sudo rm -Rf openwsn-fw
sudo rm -Rf openwsn-fw-dagroot
sudo git clone $REPO_FW
mv openwsn-fw openwsn-fw-dagroot
sudo rm -Rf openwsn-fw-device
sudo rm -Rf openwsn-fw-device
sudo git clone $REPO_FW
mv openwsn-fw openwsn-fw-device


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
cd cli-tools
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


# Packages
echo "------------------------"
echo "Installing arm"
cd $REP

echo "You have to install gcc-arm-none-eabi (sudo apt install gcc-arm-none-eabi, or download the latest version at https://developer.arm.com/"




# iotlab ssh tools
echo "-------------------------------"
echo "IoTLab Clitools (ssh)"
cd $REP
sudo rm -Rf ssh-cli-tools
git clone https://github.com/iot-lab/ssh-cli-tools.git
cd ssh-cli-tools
sudo pip install pip --upgrade
sudo apt-get install virtualenvwrapper
sudo apt-get install python-dev libssh2.1-dev
sudo pip install .
