#!/usr/bin/env python
# coding: utf-8

# In[1]:


import string
import random
import os
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
import threading
import psutil
import sys
import json, sys
import time
import sys
import signal
import tempfile
import shutil

#custom libraries
import experiments

def configuration_set():
    config = {}

    config['path_initial'] = os.getcwd()
    print ("Inital path: {0}".format(config['path_initial']))
    
    #tmp files
    config['path_tmp'] = tempfile.mkdtemp(prefix="openwsn-")
    print("Temporary path: {0} ".format(config['path_tmp']))

    # Metadata for experiments
    config['user']="theoleyr"
    config['exp_name']="owsn-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    config['exp_duration']="180"
    config['exp_resume']=True

    # Parameters of the experiment
    config['board']="iot-lab_M3"
    config['toolchain']="armgcc"
    config['archi']="m3"
    config['site']="strasbourg"
    config['nodes_list']=[ 60 , 64 ]
    config['dagroots_list']=[ 43 ]

    #openvisualizer configuration (output + 2 inputs)
    config['conf_file']= config['path_tmp'] + "/logging.conf"
    config['conf_file_start']= config['path_initial'] + "/loggers/logging_start.conf"
    config['conf_file_end']= config['path_initial'] + "/loggers/logging_end.conf"

    #parameters for the code
    config['badmaxrssi'] = 100
    config['goodminrssi'] = 100

    #Only in simulation mode!
    if ( config['board'] == "python"):
        config['nbnodes']="5"
        config['topology']="---load-topology " + config['path_initial'] + "/topologies/topology-3nodes.json"

    #code (git repositories)
    config['code_sw_src']= config['path_initial'] + "/../openvisualizer/"
    config['code_sw_gitversion']="e039a05"
    config['code_fw_src']= config['path_initial'] + "/../openwsn-fw/"
    config['code_fw_gitversion']="515eafa7"
    config['code_fw_bin']=config['code_fw_src']+"build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog"

    return(config)



#prints the headers of a section
def print_header(msg):
    print("\n\n---------------------------------------------")
    print("     " + msg)
    print("---------------------------------------------\n\n")



#signal protection
def kill_all(sig, frame):
    print(frame)

    print_header("Cleanup")
  
    print("Destroys the tmp directoy {0} (has to be rather moved)".format(config['path_tmp']))
    shutil.rmtree(config['path_tmp'])
    
    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        print("killing {0}".format(proc))
        proc.kill()
        print("..killed")
    sys.exit(0)





# ----- INIT

print_header("Initialization")

#protection against control+c (or called via a signal at the end)
signal.signal(signal.SIGINT, kill_all)

# initialiation
experiments.root_verif()
config = configuration_set()
experiments.openvisualizer_install(config)






# ---- RESERVATION /RESUME EXPERIMENT ----
print_header("Reservation (experiment)")
if ( config['exp_resume'] == True):
    exp_id = experiments.get_running_id(config);
    
try:
    print("Resume the experiment id {0}".format(exp_id))
    
except:
    experiments.reserve(config)
experiments.wait_running(exp_id)




# ---- COMPIL + FLASHING----


print_header("Compilation")
experiments.compilation_firmware(config)

print_header("Flashing")
experiments.flashing_motes(exp_id, config)




# ---- OpenVisualizer ----

print_header("Openvizualiser")

experiments.openvisualizer_create_conf_file(config)
experiments.openvisualizer_start(config)




# ---- Openweb server ----

print_header("Openweb server")
experiments.openwebserver_start(config)



# ---- Boots the motes ----

print_header("Configure Motes")
experiments.mote_boot(exp_id)
experiments.dagroot_set(config)



# ---- Exp running ----

print_header("Execution")
print("gpid me: {0}".format(os.getpgid(os.getpid())))
print("pid me: {0}".format(os.getpid()))

time.sleep(int(config['exp_duration']))
os.kill(os.getpid(), signal.SIGINT)

