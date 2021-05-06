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



# -----  Run external commands ---

#Run an extern command and returns the stdout
def run_command(cmd, path=None, shell=True):
    process = Popen(cmd, preexec_fn=os.setsid, shell=shell, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=True, cwd=path, encoding='utf-8', errors='replace', bufsize=1)
    return(process)

#Run an extern command and prints the stdout
def run_command_print(cmd, path=None, shell=True):
    process = run_command(cmd, path, shell)

    
    while process.poll() is None:
        out, err = process.communicate()
        if out is not None:
            print(out)
        if err is not None:
            print(err)

    if (process.wait() != 0):
        print("... shell command non zero retcode")
    else:
        print("... shell command finished")




#sudo verification
def root_verif():
    if (os.getuid() != 0):
        print("\n\n---------------------------------------------")
        print("      Error")
        print("---------------------------------------------\n\n")

        print("You must be root to run this script")
        print("{0} != 0".format(os.getuid()))
        sys.exit(2)






#----- Experiments control


#compiles a firmware
def compilation_firmware(config):
    cmd="scons board=" + config['board'] + " toolchain=" + config['toolchain'] + " "
    cmd=cmd +" boardopt=printf modules=coap,udp apps=cjoin,cexample debugopt=CCA,schedule "
    cmd=cmd + " scheduleopt=anycast,lowestrankfirst "
    cmd=cmd + " stackcfg=badmaxrssi:"+str(config['badmaxrssi'])+",goodminrssi:"+str(config['goodminrssi']) + " "
    cmd=cmd + " oos_openwsn "
    
    run_command_print(cmd=cmd, path=config['code_fw_src'], shell=True)



# get the iotlab id for a runnning experiment (to resume it)
def get_running_id(config):
    cmd = 'iotlab-experiment get -e'
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    infos = json.loads(output)

    # pick the last (most recent) experiment
    try:
        exp_id_running=infos["Running"][-1]
        
        #Site identification (if the experiment is already running)
        cmd="iotlab-experiment get -i " + str(exp_id_running) + " -n"
        process = run_command(cmd=cmd)
        output = process.stdout.read()
        
    except:
        print("error {0}".format(sys.exc_info()[0]))
        print("No running experiment")
        return
        #nothing returned
    
    #to verify that the experiment is matching with my params
    infos=json.loads(output)
    exp_site=infos["items"][0]["site"]
    if (config['site'] != exp_site):
        print("the site of the running experiment doesn't match: {0} != {1}".format(config['site'], exp_site))
    
    #nodes identification
    print("Running nodes:")
    for node in infos["items"]:
        print("  -> {0}".format(node["network_address"]))
        sp = node["network_address"].split(".")
        sp2 = sp[0].split("-")
        node_id = int(sp2[1])
        if node_id not in config['dagroots_list']:
            if node_id not in config['nodes_list']:
                print("     {0} is present neither in {1} nor in {2}".format(
                    sp2[1],
                    config['dagroots_list'],
                    config['nodes_list']
                ))
                return
            else:
                print("     {0} is a node (in {1})".format(node_id, config['nodes_list']))
        else:
            print("     {0} is a dagroot (in {1})".format(node_id, config['dagroots_list']))

    return(exp_id_running)


# start a novel experiment with the right config
def reserve(config):
    exp_id_running=0
    cmd= "iotlab-experiment submit " + " -n "+config['exp_name']
    cmd=cmd + " -d "+ config['exp_duration']
    cmd=cmd + " -l "+ config['site'] + "," + config['archi'] + ","
    for i in range(len(config['dagroots_list'])):
        if ( i != 0 ):
            cmd=cmd+"+"    
        cmd= cmd + str(config['dagroots_list'][i])
    for node in config['nodes_list'] :
        cmd= cmd + "+" + str(node)
    
    print(cmd)
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    print(output)
    infos=json.loads(output)
    exp_id_running=infos["id"]
    return(exp_id_running)


# waits that the id is running
def wait_running(exp_id):
    cmd="iotlab-experiment wait -i "+ str(exp_id)
    print(cmd)
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    print(output)





#Flashing the devices with a compiled firmware
def flashing_motes(exp_id, config):
    cmd="iotlab-node --flash " + config['code_fw_bin'] + " -i " + str(exp_id)
    print(cmd)
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    infos=json.loads(output)
    ok=True
    if "0" in infos:
        for info in infos["0"]:
            print("{0}: ok".format(info))

    if "1" in infos:
        for info in infos["1"]:
            print("{0}: ko".format(info))
            ok = False
    if ( ok == False ):
        print("Some motes have not been flashed correctly, stop now")
        exit(6)




#install the last version of OV (present in the code_sw_src directory
def openvisualizer_install(config):
    print("Install the current version of Openvisualizer")
    cmd="pip install -e ."
    process = run_command(cmd=cmd, path=config['code_sw_src'])
    output = process.stderr.read()
    print(output)
    if (process.wait() != 0):
        print("Installation of openvisualizer has failed")
        exit(-7)
    else:
        print("Installation ok")



#generated the configuration file (for logging)
def openvisualizer_create_conf_file(config):
    #construct the config file
    file=open(config['conf_file'], 'w')
            
    # constant beginning
    file_start=open(config['conf_file_start'], 'r')
    for line in file_start:
        file.write(line)
    file_start.close()

    file.write("[handler_std]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server.log', 'w')\n")
    file.write("formatter=std\n\n")

    file.write("[handler_errors]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server-errors.log', 'w')\n")
    file.write("level=ERROR\n")
    file.write("formatter=std\n\n")

    file.write("[handler_success]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server-success.log', 'w')\n")
    file.write("level=SUCCESS\n")
    file.write("formatter=std\n\n")

    file.write("[handler_info]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server-info.log', 'w')\n")
    file.write("level=INFO\n")
    file.write("formatter=std\n\n")

    file.write("[handler_all]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server-all.log', 'w')\n")
    file.write("formatter=std\n\n")

    file.write("[handler_html]\n")
    file.write("class=logging.FileHandler\n")
    file.write("args=('"+config['path_results']+"/openv-server-all.html.log', 'w')\n")
    file.write("formatter=console\n\n")

    #constant end
    file_end=open(config['conf_file_end'], 'r')
    for line in file_end:
        file.write(line)
    file_end.close()

    #end of the config file
    file.close()




# starts the openvisualizer as a thread (returns only when it is in running mode)
def openvisualizer_start(config):

    #construct the command with all the options for openvisualizer
    openvisualizer_options="--opentun --wireshark-debug --mqtt-broker 127.0.0.1 -d --fw-path /home/theoleyre/openwsn/openwsn-fw"
    openvisualizer_options=openvisualizer_options+ " --lconf " + config['conf_file']
    if (config['board'] == "iot-lab_M3" ):
        cmd="python /usr/local/bin/openv-server " + openvisualizer_options + " --iotlab-motes "
        for i in range(len(config['dagroots_list'])):
            cmd=cmd + config['archi'] + "-" + str(config['dagroots_list'][i]) + "." + config['site'] + ".iot-lab.info "
        for i in range(len(config['nodes_list'])):
            cmd=cmd + config['archi'] + "-" + str(config['nodes_list'][i]) + "." + config['site'] + ".iot-lab.info "
        print(cmd)
    elif (config['board'] == "python" ):
        cmd="python /usr/local/bin/openv-server " + openvisualizer_options + " --sim "+ config['nb_nodes'] + " " + config['topology']

    # stops the previous process
    try:
        print("Previous process: {0}".format(process_openvisualizer))
        process_openvisualizer.terminate()
    except NameError:
        print("No running openvisualizer process")
    except:
        print("No running openvisualizer process, error {0}".format(sys.exc_info()[0]))
        
    #Running the OV application
    print("Running openvisualizer in a separated process")
    t_openvisualizer = threading.Thread(target=run_command_print, args=(cmd, config['code_sw_src'], ))
    t_openvisualizer.start()
    print("Thread {0} started".format(t_openvisualizer))


    #wait that openvizualizer is properly initiated
    cmd="openv-client motes"
    while True:
        process = run_command(cmd=cmd)
        output = process.stdout.read()
        if "Connection refused" not in output:
            break
        #wait 2 seconds before trying to connect to the server
        time.sleep(2)
    print("Openvisualizer seems correctly running")

    return(t_openvisualizer)


#start the web client part
def openwebserver_start(config):

    cmd="python /usr/local/bin/openv-client view web --debug ERROR"
    print(cmd)
    print("Running openweb server in a separated thread")
    t_openwebserver = threading.Thread(target=run_command_print, args=(cmd, config['code_sw_src'], ))
    t_openwebserver.start()
    print("Thread {0} started, pid {1}".format(t_openwebserver, os.getpid()))

    return(t_openwebserver)


#reboot all the motes (if some have been already selected dagroot for an unkwnon reason)
def mote_boot(exp_id):
    cmd="iotlab-node --reset -i "+ str(exp_id)
    print(cmd)
    process = run_command_print(cmd=cmd)




# Configuration: dagroot
def dagroot_set(config):
    for node in config['dagroots_list']:
        cmd="openv-client root m3-" + str(node) +  "." + config['site'] + ".iot-lab.info"
        print(cmd)
        process = run_command_print(cmd=cmd)






