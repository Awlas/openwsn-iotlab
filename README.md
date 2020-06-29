# openwsn-iotlab
Here are a few scripts to handle an experiment executing openwsn:

- mirroring the two fimrware directories for dagroot and devices
- reserve automatically an experiment, or resume an already running experiment if one exists
- compile the firmware (two different directories for the dagroot and the devices to not recompile everything for each call)
- flash the motes
- set up an ssh tunnel to the iotlab server (on the right site) to tunnel all the serials from the different motes
- map the serial ports (through ssh) to a ttyUSB pseudo device locally


# requirements 
You must install Python3.6 or Python 2.7

- sudo apt-get install python3
- sudo apt-get install python3-pip

# install

To install everything, you just have to run the script: 

```
sudo ./install.sh
```

NB : you may specify other github repositories directly in install.sh (if you dont want to use my GitHub forked repositories). 

Don't forget to remove the password for the sudo commands:

```
/etc/sudoers
%sudo ALL=(ALL) NOPASSWD: ALL
```


# Usage

To execute the whole pipeline:

- mirroring 
- compilation 
- testbed reservation ([https://www.iot-lab.info/](https://www.iot-lab.info/))
- flashing the motes (first one = DAGroot)
- redirect TCP ports of the motes inside a ssh tunnel

You just have to execute `./start_and_flash.sh`

