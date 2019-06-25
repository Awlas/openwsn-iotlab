# openwsn-iotlab
Here are a few scripts to handle an experiment executing openwsn:
- reserve automatically an experiment, or resume an already running experiment if one exists
- compile the firmware (two different directories for the dagroot and the devices to not recompile everything for each call)
- flash the motes
- set up an ssh tunnel to the iotlab server (on the right site) to tunnel all the serials from the different motes
- map the serial ports (through ssh) to a ttyUSB pseudo device locally


# requirements 
You must install Python3.6 or Python 2.7
sudo apt-get install python3
sudo apt-get install python3-pip

