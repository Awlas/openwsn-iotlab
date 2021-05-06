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
import jsonpickle



#custom libraries
import experiments

#configuration for the experimenal setup (what stays unchanged)
def configuration_set():
    config = {}

    config['path_initial'] = os.getcwd()
    print ("Inital path: {0}".format(config['path_initial']))
    
    # Metadata for experiments
    config['user']="theoleyr"
    config['exp_duration']="30"
    config['exp_resume']=True
    config['exp_name']="owsn-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Parameters of the experiment
    config['board']="iot-lab_M3"
    config['toolchain']="armgcc"
    config['archi']="m3"
    config['site']="strasbourg"

    #code (git repositories)
    config['code_sw_src']= config['path_initial'] + "/../openvisualizer/"
    config['code_sw_gitversion']="e039a05"
    config['code_fw_src']= config['path_initial'] + "/../openwsn-fw/"
    config['code_fw_gitversion']="515eafa7"
    config['code_fw_bin']=config['code_fw_src']+"build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog"
    
    
    #Only in simulation mode!
    if (config['board'] == "python"):
        config['nbnodes']="5"
        config['topology']="---load-topology " + config['path_initial'] + "/topologies/topology-3nodes.json"

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
  
    if (sig == signal.SIGUSR1):
        print("Everything was ok")
        file = open(config['path_results'] + "/_ok.txt", 'w')
        file.write("ok\n")
        file.close()
    else:
        print("Something went wrong -> move the files {0} in {1}". format(config['path_results'], config['path_results_root']+"crash"))
        shutil.move(config['path_results'], config['path_results_root_crash'])

    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        print("killing {0}".format(proc))
        proc.kill()
        print("..killed")
    if (sig == signal.SIGINT):
        sys.exit(0)
    else:
        sys.exit(3)
 




# ----- INIT

print_header("Initialization")

#protection against control+c (or called via a signal at the end)
signal.signal(signal.SIGINT, kill_all)
signal.signal(signal.SIGUSR1, kill_all)


# initialiation
experiments.root_verif()
config = configuration_set()
experiments.openvisualizer_install(config)



print_header("Fixed parameters")


#Parameters for this set of experiments
# list of motes
config['nodes_list']=[ 60 , 64 ]
config['dagroots_list']=[ 43 ]

#parameters for the code
config['badmaxrssi'] = 100
config['goodminrssi'] = 100





# ---- RESERVATION /RESUME EXPERIMENT ----
print_header("Reservation (experiment)")
if ( config['exp_resume'] == True):
    exp_id = experiments.get_running_id(config);
if exp_id is not None:
    print("Resume the experiment id {0}".format(exp_id))
else:
    exp_id = experiments.reserve(config)
experiments.wait_running(exp_id)






# test the two different solutions
anycast_list = [False , True]
for anycast in anycast_list:
    
    print_header("Anycast = " + str(anycast))
    
    #final results
    config['path_results_root'] = "/home/theoleyre/owsn-results/"
    config['path_results_root_crash'] = config['path_results_root'] + "/crash"
    os.makedirs(config['path_results_root_crash'], exist_ok=True)
    it = os.listdir(config['path_results_root'])
    while (True):
        config['path_results'] = "owsn-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        print("List of existing results: {0}".format(it))
        if (config['path_results'] not in it):
            break;
        print("{0} laready exists, find another directory name.".format(config['path_results']))
    config['path_results'] = config['path_results_root'] + config['path_results']
    os.makedirs(config['path_results'])
    print("Results Path {0}".format(config['path_results']))


    # ---- CONFIG----
 
    #openvisualizer configuration (output + 2 inputs)
    config['conf_file']= config['path_results'] + "/logging.conf"
    config['conf_file_start']= config['path_initial'] + "/loggers/logging_start.conf"
    config['conf_file_end']= config['path_initial'] + "/loggers/logging_end.conf"

     #param
    config['anycast'] = anycast

    #saves the config
    file = open(config['path_results']+"/params.txt", 'w')
    str = jsonpickle.encode(config)
    file.write(str)
    file.close
    

    # ---- COMPIL + FLASHING----


    print_header("Compilation")
    experiments.compilation_firmware(config)

    print_header("Flashing")
    experiments.flashing_motes(exp_id, config)




    # ---- OpenVisualizer ----

    print_header("Openvizualiser")

    experiments.openvisualizer_create_conf_file(config)
    t_openvisualizer = experiments.openvisualizer_start(config)




    # ---- Openweb server (optional, for debuging via a web interface) ----

    #print_header("Openweb server")
    #t_openwebserver = experiments.openwebserver_start(config)



    # ---- Boots the motes ----

    print_header("Configure Motes")
    experiments.mote_boot(exp_id)
    experiments.dagroot_set(config)



    # ---- Exp running ----

    print_header("Execution")
    print("gpid me: {0}".format(os.getpgid(os.getpid())))
    print("pid me: {0}".format(os.getpid()))

    print("nb threads = {0}".format(threading.active_count()))

    #every second, let us verify that the openvizualizer thread is still alive
    #TODO: transform minutes in seconds
    counter = 0
    while (t_openvisualizer.is_alive()):
        print("thread {0} is alive, {1}<{2}".format(t_openvisualizer, counter, int(config['exp_duration'])))
        counter = counter + 1
        if (counter >= int(config['exp_duration'])):
            break;
        time.sleep(1)
        

    print("nb seconds runtime: {0}".format(counter))





#time.sleep(60 * int(config['exp_duration']))
if (counter >= int(config['exp_duration'])):
    os.kill(os.getpid(), signal.SIGUSR1)
else:
    os.kill(os.getpid(), signal.SIGINT)

