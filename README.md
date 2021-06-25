# openwsn-iotlab
Here are a few scripts to handle an experiment executing openwsn:

- mirroring the two fimrware directories for dagroot and devices
- reserve automatically an experiment, or resume an already running experiment if one exists
- compile the firmware (two different directories for the dagroot and the devices to not recompile everything for each call)
- flash the motes
- set up an ssh tunnel to the iotlab server (on the right site) to tunnel all the serials from the different motes
- map the serial ports (through ssh) to a ttyUSB pseudo device locally


# installation

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

## Dependencies

This tool set depends on:

- [https://github.com/ftheoleyre/openwsn-iotlab](https://github.com/ftheoleyre/openwsn-iotlab): all the tools to reserve experiments through FIT IoLab, flash firmware, compile the sofware, start openvisualizer, get data, etc.
- [https://github.com/ftheoleyre/openwsn-fw](https://github.com/ftheoleyre/openwsn-fw): the firmware (in C)
- [https://github.com/ftheoleyre/openvisualizer](https://github.com/ftheoleyre/openwsn-iotlab): the software on the PC side (to get the statistics, configure the motes, monitor everything)
-  [https://github.com/ftheoleyre/openwsn-data](https://github.com/ftheoleyre/openwsn-data): process the data (cexample packets) generated by an experience and collected with openvisualizer in a sqlite DB (end-to-end PDR, # of packets, delays, etc.)


## Python
You must install Python3 (for the scripts), and Python 2.7 (for openvisualizer)

```
sudo apt-get install python3
sudo apt-get install python3-pip
```



# Usage

To execute the whole experiment pipeline:

- one random subdirectory per experiment to save the log files + the sqlite DB 
- experiment reservation ([https://www.iot-lab.info/](https://www.iot-lab.info/)) with the right set of motes
- compilation with the right parameters
- flashing the motes (first one = DAGroot)
- redirect TCP ports of the motes inside a ssh tunnel
- starting openvisualizer that collects the statistics in a sqlite database

NB: the same experiment is used for comparing the solutions (i.e., the set of devices does not change for all the protocols we want to compare)


You just have to execute 

```
cd scripts
sudo python3 run_experiments.py
```

