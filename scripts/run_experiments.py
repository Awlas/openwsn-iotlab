#!/usr/bin/env python
# coding: utf-8



# systems tools
import os
import shutil
import sys
import time
import sys
import signal
import random

# multiprocess
import threading
import psutil

#format
import string
import json

#custom libraries
import iotlabowsn



#configuration for the experimenal setup (what stays unchanged)
def configuration_set():
    config = {}

    #paths
    config['path_initial'] = os.getcwd()
    print ("Inital path: {0}".format(config['path_initial']))
    
    config['path_results_root'] = "/home/theoleyre/openwsn/results/"
    config['path_results_root_crash'] = config['path_results_root'] + "/crash"
    os.makedirs(config['path_results_root_crash'], exist_ok=True)
    
    # Metadata for experiments
    config['user']="theoleyr"
    config['exp_duration']=180        # for the iot lab reservation (collection of runs), in minutes
    config['subexp_duration']=1       # for one run (one set of parameters), in minutes
    config['exp_resume']=True
    config['exp_name']="owsn-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Parameters of the experiment
    config['board']="iot-lab_M3"
    config['toolchain']="armgcc"
    config['archi']="m3"
    config['site']="grenoble"
    config['maxid']=289             #discard larger node's ids
    config['minid']=70              #discard smaller node's ids
  
    # list of motes
    #config['nodes_list']=[ 60 , 64 ]       #selected at runti, depending on the platform state
    #config['dagroots_list']=[ 43 ]

    
    # openvisualizer directory
    config['code_sw_src'] = config['path_initial'] + "/../openvisualizer/"
    if (os.path.exists(config['code_sw_src']) == False):
        print("{0} does not exist".format(config['code_sw_src']))
        exit(-4)
    config['code_sw_gitversion']="525b684"

    # firmware part
    config['code_fw_src']= config['path_initial'] + "/../openwsn-fw/"
    if (os.path.exists(config['code_fw_src']) == False):
        print("{0} does not exist".format(config['code_fw_src']))
        exit(-4)
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


#clean up
def cleanup_subexp(error=False):
    print_header("Cleanup")

    if (error == False):
        print("Everything was ok")
        file = open(config['path_results'] + "/_ok.txt", 'w')
        file.write("ok\n")
        file.close()
    else:
        print("Something went wrong -> move the files {0} in {1}". format(config['path_results'], config['path_results_root']+"crash"))
        shutil.move(config['path_results'], config['path_results_root_crash'])
        
    del config['path_results']
    
        
#signal protection
def kill_all(sig, frame):
  
    #cleanup the directory result
    if 'path_results' in config:
        cleanup_subexp(sig == signal.SIGUSR1)
    #stop the experiment (iotlab)
    if exp_id != 0:
        iotlabowsn.exp_stop(exp_id)

    #kill everything
    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        print("killing {0}".format(proc))
        proc.kill()
        print("..killed")
    if (sig == signal.SIGUSR1):
        sys.exit(0)
    else:
        sys.exit(3)
 




# ----- INIT


print_header("Initialization")
iotlabowsn.root_verif()
config = configuration_set()
config['seed'] = 2
random.seed(config['seed'])


#openvisualizer
iotlabowsn.openvisualizer_install(config)


#Parameters for this set of experiments
config['badmaxrssi'] = 100
config['goodminrssi'] = 100
config['lowestrankfirst'] = 1


#construct the list of motes
print_header("Nodes Selection")
testbed_nodealive_list = iotlabowsn.get_nodes_list(config["site"], config["archi"], "Alive")
maxspace_between_ids=15
nbnodes=10
nbtest=0
config['nodes_list'] = []

#insert iteratively the motes
while(len(config['nodes_list']) < nbnodes):
    connected = False
    while(connected is False):
    
        #pick a random id in the list (not already present in the selection
        while (True):
            new = random.randint(0, len(testbed_nodealive_list)-1)
            new = int(testbed_nodealive_list[new])
            
            #this id is a priori ok
            if ((new >= config['minid']) and (new <= config['maxid']) and (new not in config['nodes_list'])):
                #print(new)
                break
                
        #print("test {0} in {1} {2}".format(new, config['nodes_list'], len(config['nodes_list'])))
        
        #the list is not null
        if (len(config["nodes_list"]) > 0):
            
            #an id in the list is close to this novel one
            for node in config['nodes_list']:
                if (abs(node - new) <= maxspace_between_ids):
                    connected = True
                    break
                
        # the first id is ok, whatever it is
        else:
            connected = True
        
        if (connected):
            config["nodes_list"].append(new)
            
        
        #too many fails -> restart from scratch
        #print("nbtest {0}".format(nbtest))
        nbtest = nbtest + 1
        if (nbtest > 15 * nbnodes):
            print("too many fails -> flush the list to start from scratch")
            config['nodes_list'].clear()
            nbtest=0


#cleanup + dagroot selection (first mote in the list)
config['nodes_list'].sort(key=int)
config['dagroots_list'] = [config['nodes_list'][0], ]
config['nodes_list'].remove(config['dagroots_list'][0])
print("Nodes list: {0}".format(config["nodes_list"]))
print("Dagroot: {0}".format(config["dagroots_list"]))




# ---- RESERVATION /RESUME EXPERIMENT ----
print_header("Reservation (experiment)")
if ( config['exp_resume'] == True):
    exp_id = iotlabowsn.get_running_id(config);
if exp_id is not None:
    print("Resume the experiment id {0}".format(exp_id))
else:
    exp_id = iotlabowsn.exp_start(config)
print("Wait the experiment is in running mode")
iotlabowsn.exp_wait_running(exp_id)


# test the two different solutions
for anycast in [False] : # , True]:
    
    print_header("Anycast = {0}".format(anycast))
    
    #final results
    dirs_res = os.listdir(config['path_results_root'])
    dirs_trash =  os.listdir(config['path_results_root_crash'])
    while (True):
        config['path_results'] = "owsn-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        print("List of existing results: {0}, {1}".format(dirs_res, dirs_trash))
        if (config['path_results'] not in dirs_res and config['path_results'] not in dirs_trash):
            break;
        print("{0} already exists, find another directory name.".format(config['path_results']))
    config['path_results'] = config['path_results_root'] + config['path_results']
    os.makedirs(config['path_results'])
    print("Results Path {0}".format(config['path_results']))


    # ---- CONFIG----
 
    #openvisualizer configuration
    config['conf_file']= config['path_results'] + "/logging.conf"
    config['conf_file_start']= config['path_initial'] + "/loggers/logging_start.conf"
    config['conf_file_end']= config['path_initial'] + "/loggers/logging_end.conf"

     #param
    config['anycast'] = anycast

    #saves the config
    file = open(config['path_results']+"/params.txt", 'w')
    json.dump(config, file)
    file.close()
    
    
    
    # ---- COMPIL + FLASHING----

    print_header("Compilation")
    iotlabowsn.compilation_firmware(config)

    print_header("Flashing")
    iotlabowsn.flashing_motes(exp_id, config)



    # ---- OpenVisualizer ----

    time_start = time.time()
    print_header("Openvizualiser")
    iotlabowsn.openvisualizer_create_conf_file(config)
    t_openvisualizer = iotlabowsn.openvisualizer_start(config)




    # ---- Openweb server (optional, for debuging via a web interface) ----

    print_header("Openweb server")
    t_openwebserver = iotlabowsn.openwebserver_start(config)



    # ---- Boots the motes ----

    print_header("Configure Motes")
    iotlabowsn.mote_boot(exp_id)
    iotlabowsn.dagroot_set(config)



    # ---- Exp running ----

    print_header("Execution")
    print("gpid me: {0}".format(os.getpgid(os.getpid())))
    print("pid me: {0}".format(os.getpid()))

    print("nb threads = {0}".format(threading.active_count()))

    #every second, let us verify that the openvizualizer thread is still alive
    counter = 0
    while (t_openvisualizer.is_alive()):
        counter = counter + 1
        if (counter >= 60):
            print("thread {0} is alive, {1}s < {2}min".format(t_openvisualizer, time.time() - time_start, config['subexp_duration']))
            counter = 0
        time.sleep(1)

    #everything was ok -> cleanup
    print("{0} >= ? {1} -> {2}".format(time.time() - time_start+2 , 60*config['subexp_duration'], time.time() - time_start +2 >= 60 * config['subexp_duration'] is not True))
    cleanup_subexp(time.time() - time_start + 2 < 60 * config['subexp_duration'])


    print("nb seconds runtime: {0}".format(time.time() - time_start))
    print("nb threads = {0}".format(threading.active_count()))
   
   
    #kill all my children (including openweb server)
    if t_openwebserver is not None and t_openwebserver.is_alive():
        print("Cleanning up children process".format(t_openwebserver))
        process = psutil.Process(os.getpid())
        for proc in process.children(recursive=True):
            print("killing {0}".format(proc))
            proc.kill()
            print("..killed")
    
    
iotlabowsn.exp_stop(exp_id)



#if we are here, this means that we don't have any other running process
print("End of the computation")
print("nb seconds runtime: {0}".format(time.time() - time_start))
print("nb threads = {0}".format(threading.active_count()))

sys.exit(0)

