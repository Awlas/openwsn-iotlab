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


#sudo verification
if (os.getuid() != 0):
    print("\n\n---------------------------------------------")
    print("      Error")
    print("---------------------------------------------\n\n")

    print("You must be root to run this script")
    print("{0} != 0".format(os.getuid()))
    sys.exit(2)


#signal protection
def kill_all(sig, frame):
    print(frame)

    print("\n\n---------------------------------------------")
    print("      Cleanup")
    print("---------------------------------------------\n\n")

    print("Destroys the tmp directoy {0} (has to be rather moved)".format(path_exp))
    shutil.rmtree(path_exp)
    
    process = psutil.Process(os.getpid())
    for proc in process.children(recursive=True):
        print("killing {0}".format(proc))
        proc.kill()
        print("..killed")
    sys.exit(0)

#protection against control+c (or called via a signal at the end)
signal.signal(signal.SIGINT, kill_all)



print("\n\n---------------------------------------------")
print("   Tmp directory")
print("---------------------------------------------\n\n")



#Paths
path_initial = os.getcwd()
print ("Inital path: {0}".format(path_initial))

#Random suffix for tmp filenames
letters = string.ascii_letters
random_suffix = ''.join(random.choice(letters) for i in range(10))
path_exp = tempfile.mkdtemp(prefix="openwsn-")
#path_exp="/tmp/openwsn-"+random_suffix
#os.mkdir(path_exp)
print("Temporary path: {0} ".format(path_exp))


# In[38]:


print("\n\n---------------------------------------------")
print("   All variables / parameters initialization")
print("---------------------------------------------\n\n")

# Metadata for experiments
iotlab_user="theoleyr"
iotlab_exp_name="owsn-" + random_suffix 
iotlab_exp_duration="180"
iotlab_resume_exp=True

# Parameters of the experiment
exp_board="iot-lab_M3"
exp_toolchain="armgcc"
exp_archi="m3"
exp_site="strasbourg"
exp_nodes_list=[ 60 , 64 ]
exp_dagroots_list=[ 43 ]

#openvisualizer configuration
exp_logging_conf=path_initial + "/loggers/logging.conf"

#Only in simulation mode!
exp_nbnodes="5"
exp_topology="---load-topology " + path_initial + "/topologies/topology-3nodes.json"
#code (git repositories)
code_sw_src=path_initial+"/../openvisualizer/"
code_sw_gitversion="e039a05"
code_fw_src=path_initial+"/../openwsn-fw/"
code_fw_gitversion="515eafa7"
code_fw_bin=code_fw_src+"build/iot-lab_M3_armgcc/projects/common/03oos_openwsn_prog"

print(".. finished")


# In[39]:


print("\n\n---------------------------------------------")
print("    Shell commands")
print("---------------------------------------------\n\n")


#Run an extern command and returns the stdout
def run_command(cmd, path=None, shell=True):
    process = Popen(cmd, preexec_fn=os.setsid, shell=shell, stdin=None, stdout=PIPE, stderr=PIPE, close_fds=True, cwd=path, encoding='utf-8', errors='replace', bufsize=1)
    return(process)

#Run an extern command and prints the stdout
def run_command_print(cmd, path=None, shell=True):
    process = run_command(cmd, path, shell)
 
 #   while True:
 #       out = process.stdout.read(1)
 #       if out == '' and process.poll() is not None:
 #           break
 #       if out != '':
 #           sys.stdout.write(out)
 #           sys.stdout.flush()
    
    
    while process.poll() is None:
        out, err = process.communicate()
        if out is not None:
            print(out)
        if err is not None:
            print(err)
        

    
        
###        print(process.poll())
#        print(process)
 
    #until the process is terminated (poll=none), get the stdout and stderr
#    while (True):
#        try:
#            out, err = process.communicate(timeout=2)
#            print("no timeout")
#            print(out)
#            print(err)
#        except TimeoutExpired:
#            out, err = process.communicate()
#            print("except timeout")
#            print(out)
#            print(err)
#        except:
#            print("Hum, unhandled error {0}".format(sys.exc_info()[0]))
#            break
#        if (process.poll() != None):
#            break;
            
#    while process.poll(timeout=1) is None:
#        out, err = process.communicate()
#        print(out)
###        print(process.poll())
#        print(process)

    if (process.wait() != 0):
        print("... non zero retcode")
    else:
        print("... finished")

print(".. finished")


# In[40]:


print("\n\n---------------------------------------------")
print("      Compilation")
print("---------------------------------------------\n\n")

#Compilation
cmd="scons board=" + exp_board + " toolchain=" + exp_toolchain + " " 
cmd=cmd +" boardopt=printf modules=coap,udp apps=cjoin,cexample debugopt=CCA,schedule "
cmd=cmd + " scheduleopt=anycast,lowestrankfirst "
badmaxrssi="100"
goodminrssi="100"
cmd=cmd + " stackcfg=badmaxrssi:"+badmaxrssi+",goodminrssi:"+goodminrssi + " "
cmd=cmd + " oos_openwsn "
run_command_print(cmd=cmd, path=code_fw_src, shell=True)


# In[41]:


print("\n\n---------------------------------------------")
print("      Reservation (experiment)")
print("---------------------------------------------\n\n")


# Let us resume an experiment (if one exists)
if (iotlab_resume_exp == True):
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
    
    infos=json.loads(output)
    exp_site=infos["items"][0]["site"]
    print("The site of this already running experiment has been identified to {0}".format(exp_site))

    #nodes identification 
    print("Running nodes:")
    for node in infos["items"]:
        print("  -> {0}".format(node["network_address"]))
    print("Be careful: this list must be equal to:")
    print("  -> dagroot(s): {0}".format(exp_dagroots_list))
    print("  -> node(s): {0}".format(exp_nodes_list))

#no experiment has been found -> let us start a novel one
except:
    print("Start an experiment")
    exp_id_running=0
    cmd= "iotlab-experiment submit " + " -n "+iotlab_exp_name + " -d "+ iotlab_exp_duration + " -l "+ exp_site + "," + exp_archi + ","
    for i in range(len(exp_dagroots_list)):    
        if ( i != 0 ):
            cmd=cmd+"+"    
        cmd= cmd + str(exp_dagroots_list[i])
    for node in exp_nodes_list :
        cmd= cmd + "+" + str(node)
    
    print(cmd)
    process = run_command(cmd=cmd)
    output = process.stdout.read()
    print(output)
    infos=json.loads(output)
    exp_id_running=infos["id"]    

#id of the experiment (alreay running or just started)
print("Experiment id running: {0}".format(exp_id_running))     


# In[42]:


print("\n\n---------------------------------------------")
print("      Waiting for a running exp")
print("---------------------------------------------\n\n")

# waiting for the running mode
print("Waiting running state")
cmd="iotlab-experiment wait -i "+ str(exp_id_running)
print(cmd)
process = run_command(cmd=cmd)
output = process.stdout.read()
print(output)    


# In[43]:


print("\n\n---------------------------------------------")
print("      Flashing")
print("---------------------------------------------\n\n")

#Flashing the devices
cmd="iotlab-node --flash " + code_fw_bin + " -i " + str(exp_id_running)
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

print(".. finished")


# In[44]:


print("\n\n---------------------------------------------")
print("      Openvisualizer installation")
print("---------------------------------------------\n\n")


#Install openvisualizer
print("Install the current version of Openvisualizer")
cmd="pip install -e ."
process = run_command(cmd=cmd, path=code_sw_src)
output = process.stderr.read()
print(output)
if (process.wait() != 0):
    print("Installation of openvisualizer has failed")
    exit(-7)
else:
    print("Installation ok")


# In[45]:


print("\n\n---------------------------------------------")
print("      Configuration file (for logs)")
print("---------------------------------------------\n\n")

#construct the config file
file=open(exp_logging_conf, 'w')
print("Configuration file ....")

try:
    os.mkdir(path_exp)
except :
    print("Directory {0} already exists".format(path_exp+""))
    
# constant beginning
file_start=open(exp_logging_conf+".start", 'r')
for line in file_start:
    file.write(line)
file_start.close()

file.write("[handler_std]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server.log', 'w')\n")
file.write("formatter=std\n\n")

file.write("[handler_errors]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server-errors.log', 'w')\n")
file.write("level=ERROR\n")
file.write("formatter=std\n\n")

file.write("[handler_success]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server-success.log', 'w')\n")
file.write("level=SUCCESS\n")
file.write("formatter=std\n\n")

file.write("[handler_info]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server-info.log', 'w')\n")
file.write("level=INFO\n")
file.write("formatter=std\n\n")

file.write("[handler_all]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server-all.log', 'w')\n")
file.write("formatter=std\n\n")

file.write("[handler_html]\n")
file.write("class=logging.FileHandler\n")
file.write("args=('"+path_exp+"/openv-server-all.html.log', 'w')\n")
file.write("formatter=console\n\n")


#constant end
file_end=open(exp_logging_conf+".end", 'r')
for line in file_end:
    file.write(line)
file_end.close()

#end of the config file
file.close()
print("... finished")



print("\n\n---------------------------------------------")
print("      Openvisualizer (start)")
print("---------------------------------------------\n\n")


#construct the command with all the options for openvisualizer
openvisualizer_options="--opentun --wireshark-debug --mqtt-broker 127.0.0.1 -d --fw-path /home/theoleyre/openwsn/openwsn-fw"
openvisualizer_options=openvisualizer_options+ " --lconf " + exp_logging_conf
if ( exp_board == "iot-lab_M3" ):
    cmd="python /usr/local/bin/openv-server " + openvisualizer_options + " --iotlab-motes "
    for i in range(len(exp_dagroots_list)):    
        cmd=cmd + exp_archi + "-" + str(exp_dagroots_list[i]) + "." + exp_site + ".iot-lab.info "
    for i in range(len(exp_nodes_list)):    
        cmd=cmd + exp_archi + "-" + str(exp_nodes_list[i]) + "." + exp_site + ".iot-lab.info "
    print(cmd)
elif ( exp_board == "python" ):
    cmd="python /usr/local/bin/openv-server " + openvisualizer_options + " --sim "+ exp_nb_nodes + " " + exp_topology

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
t_openvisualizer = threading.Thread(target=run_command_print, args=(cmd, code_sw_src, ))
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


# In[56]:


print("\n\n---------------------------------------------")
print("      OpenWeb Server")
print("---------------------------------------------\n\n")


#start the web client part 
cmd="python /usr/local/bin/openv-client view web --debug ERROR"
print(cmd)
print("Running openweb server in a separated thread")
t_openwebserver = threading.Thread(target=run_command_print, args=(cmd, code_sw_src, ))
t_openwebserver.start()
print("Thread {0} started, pid {1}".format(t_openwebserver, os.getpid()))


# In[48]:


print("\n\n---------------------------------------------")
print("      Booting the motes")
print("---------------------------------------------\n\n")

#reboot all the motes (if some have been already selected dagroot for an unkwnon reason)
print("Boot all the motes")
if ( exp_board == "iot-lab_M3" ):
    cmd="iotlab-node --reset -i "+ str(exp_id_running)
    print(cmd)
    process = run_command_print(cmd=cmd)

print("...finished")


# In[55]:



print("\n\n---------------------------------------------")
print("      DAGroot activation motes")
print("---------------------------------------------\n\n")

# Configuration: dagroot
if ( exp_board == "iot-lab_M3" ):
    for node in exp_dagroots_list:
        cmd="openv-client root m3-" + str(node) +  "." + exp_site + ".iot-lab.info"
        print(cmd)
        process = run_command_print(cmd=cmd)

print("...finished")


# In[55]:


print("\n\n---------------------------------------------")
print("      Dagroot activation")
print("---------------------------------------------\n\n")

# Configuration: dagroot
#if ( exp_board == "iot-lab_M3" ):
#    for node in exp_dagroots_list:
#        cmd="openv-client root m3-" + str(node) +  "." + exp_site + ".iot-lab.info"
#        print(cmd)
#        process = run_command(cmd=cmd)
#        output = process.stdout.read()
#        print(output)
#        if "Ok"  not in output:
#            print("Error when setting up the dagroot {0}".format(node))


# In[53]:


print("\n\n---------------------------------------------")
print("      Execution")
print("---------------------------------------------\n\n")

print("Wait for the end of the experiment")
time.sleep(1)



# In[ ]:


print("\n\n---------------------------------------------")
print("      End of the experiment")
print("---------------------------------------------\n\n")

print("gpid me: {0}".format(os.getpgid(os.getpid())))
print("pid me: {0}".format(os.getpid()))



#wait for the end of the experiment
time.sleep(int(iotlab_exp_duration))

os.kill(os.getpid(), signal.SIGINT)
#never reached here


sys.exit(0)


#for timeout
def handler_alarm(signum, frame):
    print('Signal handler called with signal', signum)
    raise OSError("Couldn't open device!")

# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGALRM, handler_alarm)
signal.alarm(5)

# This open() may hang indefinitely
fd = os.open('/dev/ttyS0', os.O_RDWR)

signal.alarm(0)          # Disable the alarm
