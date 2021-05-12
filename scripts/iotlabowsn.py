#!/usr/bin/env python
# coding: utf-8


#files
import subprocess

# format
import string
import json
import array

# multiprocess
import threading

#systems
import os
import sys
import sys
import time




# -----  Run external commands ---

#Run an extern command and returns the stdout
def run_command(cmd, timeout=0, path=None):
    
    process = subprocess.Popen(cmd, preexec_fn=os.setsid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, cwd=path, universal_newlines=True, bufsize=0)
    
    #after the timeout, kill all the children (Shell=True)
    if (timeout > 0):
        time_start = time.time()
        while (True):
            try:
                out, err = process.communicate(timeout=5)
                print(out)
                print(err)
                print("-------")
                   
                #that's the end
                if process.poll() is not None:
                    print("The process has correctly terminated before the timeout")
                    break;
                
            except subprocess.TimeoutExpired:
                # timeout !
                if (time.time() - time_start > timeout):
                    print("run_command(), timeout expiration, pid {0}".format(process.pid))
                        
                    import psutil
                    process_me = psutil.Process(process.pid)
                    for proc in process_me.children(recursive=True):
                        print("killing {0}".format(proc))
                        proc.kill()
                        print("..killed")
                # the process is terminated
                elif process.poll() is not None:
                    print("The process has correctly terminated before the timeout")
                    break;
                
                #still time to run
                else:
                    print("we still have time: {0}s < {1}s".format(time.time() - time_start, timeout))
    else:
        process.wait()
      
        
    #if (process.returncode != 0):
    #    print("Return code after run() {0}".format(process.returncode))
    return(process)
    

#Run an extern command and prints the stdout
def run_command_print(cmd, timeout=0, path=None):
    process = run_command(cmd, timeout, path)

    if (timeout == 0):
        print("STDOUT= {0}".format(process.stdout.read()))
        print("STDERR= {0}".format(process.stderr.read()))

    return(process)


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
    if (config['anycast'] and config['lowestrankfirst']):
        cmd=cmd + " scheduleopt=anycast,lowestrankfirst "
    elif (config['anycast']):
        cmd=cmd + " scheduleopt=anycast "
    cmd=cmd + " stackcfg=badmaxrssi:"+str(config['badmaxrssi'])+",goodminrssi:"+str(config['goodminrssi']) + " "
    cmd=cmd + " oos_openwsn "
    
    print(cmd)
    run_command_print(cmd=cmd, path=config['code_fw_src'])



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
    except KeyError:
        print("No running experiment")
        return
    except:
        print("No running experiment, error {0}".format(sys.exc_info()[0]))
        return
        #nothing returned
    
    #to verify that the experiment is matching with my params
    infos=json.loads(output)
    exp_site=infos["items"][0]["site"]
    if (config['site'] != exp_site):
        print("the site of the running experiment doesn't match: {0} != {1}".format(config['site'], exp_site))
    
    #nodes identification
    print("Verification that the list of nodes is correct for the exp_id {0}".format(exp_id_running))
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
def exp_start(config):
    exp_id_running=0
    cmd= "iotlab-experiment submit " + " -n "+config['exp_name']
    cmd=cmd + " -d "+ str(config['exp_duration'])
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
def exp_wait_running(exp_id):
    cmd="iotlab-experiment wait -i "+ str(exp_id)
    print(cmd)
    process = run_command(cmd=cmd)
    print(process.stdout.read())

# waits that the id is running
def exp_stop(exp_id):
    cmd="iotlab-experiment stop -i "+ str(exp_id)
    print(cmd)
    process = run_command(cmd=cmd)
    print(process.stdout.read())


def get_nodes_list(site, archi, state):
    nodes_list = []
    
    cmd="iotlab-status --nodes --site "+site+" --archi "+archi+" --state "+state
    print(cmd)
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    infos=json.loads(output)
    l_net = infos["items"][1]["network_address"]
    for item in infos["items"]:
        node = item["network_address"].split('.')[0].split('-')[1]
        nodes_list.append(node)
    nodes_list.sort(key=int)
    return(nodes_list)
    
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
    cmd="pip2 install -e ."
    process = run_command(cmd=cmd, path=config['code_sw_src'])
    for line in process.stderr:
        print(line)
    
    
    if (process.returncode != 0):
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
        print("openvisualizer_start, No running openvisualizer process, error {0}".format(sys.exc_info()[0]))
        
    #Running the OV application
    print("Running openvisualizer in a separated process")
    if ('subexp_duration' in config):
        t_openvisualizer = threading.Thread(target=run_command_print, args=(cmd, config['subexp_duration'] * 60, config['code_sw_src'], ))
    else:
        t_openvisualizer = threading.Thread(target=run_command_print, args=(cmd, 0, config['code_sw_src'], ))
    t_openvisualizer.start()
    print("Thread {0} started".format(t_openvisualizer))


    #wait that openvizualizer is properly initiated
    cmd="openv-client motes"
    while True:
        process = run_command(cmd=cmd)
        output = process.stdout.read()
        #print(output)
        #print(output.find("Connection refused"))
        
        #connected -> openvisualizer is running
        if output.find("Connection refused") == -1:
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
    if ('subexp_duration' in config):
        t_openwebserver = threading.Thread(target=run_command_print, args=(cmd, config['subexp_duration'] * 60, config['code_sw_src'],))
    else:
          t_openwebserver = threading.Thread(target=run_command_print, args=(cmd, 0, config['code_sw_src'],))

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






