# openwsn-iotlab

![](https://img.shields.io/badge/python-3.9-green)
![](https://img.shields.io/badge/python-2.7-green)


Here are a few scripts to handle an experiment executing openwsn:

- mirroring the two fimrware directories for dagroot and devices
- reserve automatically an experiment, or resume an already running experiment if one exists
- compile the firmware (two different directories for the dagroot and the devices to not recompile everything for each call)
- flash the motes
- set up an ssh tunnel to the iotlab server (on the right site) to tunnel all the serials from the different motes
- map the serial ports (through ssh) to a ttyUSB pseudo device locally

## Dependencies

This tool set depends on:

- [https://github.com/iot-lab/cli-tools](https://github.com/iot-lab/cli-tools) and [https://github.com/iot-lab/ssh-cli-tools](https://github.com/iot-lab/ssh-cli-tools): all the tools to provide a basic set of operations for managing IoT-LAB experiments from the command-line.
- [https://github.com/openwsn-berkeley/openwsn-fw](https://github.com/openwsn-berkeley/openwsn-fw): the firmware (in C)
- [https://github.com/openwsn-berkeley/openvisualizer](https://github.com/openwsn-berkeley/openvisualizer): the software on the PC side (to get the statistics, configure the motes, monitor everything)

### Python
You must install Python3 (for the scripts), **and** Python 2.7 (for openvisualizer)

```
sudo apt-get install python3
sudo apt-get install python3-pip
```

## Installation

You can use directly the [iotlab-experiments docker image](https://hub.docker.com/r/awlas/iotlab-experiments) that contains all the depedencies needed to use this project. This image contains also this repository. 

# Usage

It executes the following pipeline:

- creation of a random subdirectory per experiment to save the log files
- experiment reservation ([https://www.iot-lab.info/](https://www.iot-lab.info/)) with the right set of motes
- compilation with the right parameters
- flashing the motes (first one = DAGroot)
- redirect TCP ports of the motes inside a ssh tunnel

NB: the same experiment is used for comparing the solutions (i.e., the set of devices does not change for all the protocols we want to compare)

You just have to execute 

```
cd scripts
sudo python3 run_experiments.py
```

## Note

Use the [iotlab-experiments docker-compose](https://github.com/Awlas/iotlab-experiments) to simplify the use of this scripts.
