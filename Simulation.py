# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 15:09:31 2019

@author: song
"""

"""
Simulation experiment

Simulation based on SimPy:  https://simpy.readthedocs.io/en/latest/
SimPy is a process-based discrete-event simulation framework based on standard Python.

"""

import soCoM
from OFFLOAD import OFFLOADQ

import random
import simpy


SIM_TIME = 150000
RANDOM_SEED = 40
RHO = 2
BUFFER = 500 

#Simulation of comparative non-RL Experiment
def Simulation(rho,name,function):
    random.seed(RANDOM_SEED)
    mec = soCoM.MEC()
    mec.RHO = rho*mec.RHO
    name += str(mec.USERS_NUM)
    print ("Envronment create!")
    env = simpy.Environment()
    print ("User create!") 
    for i in range(mec.USERS_NUM):
        user = soCoM.User(i)
        user.usersetting()
        user.usercreat()
        mec.USER_LIST.append(user)

    WAITING_LEN = simpy.Container(env,BUFFER, init=len(mec.WAITING_LIST))
    
    env.process(mec.runremote(env,WAITING_LEN))
    env.process(mec.refreshsys(env,WAITING_LEN,name,'rho'+str(mec.RHO),1))
    if function == 'offline':
        env.process(mec.offloadOF(env,WAITING_LEN))
    elif function == 'online':
        env.process(mec.offloadOL(env,WAITING_LEN))
    elif function == 'Semi':
        env.process(mec.offloadSe(env,WAITING_LEN))
    
    env.process(mec.writelog(env,name,'rho',int(mec.RHO)))

    env.run(until=SIM_TIME)
    
    mec.writeoffload(name,'rho',int(mec.RHO))
    for u in mec.USER_LIST:
        u.userprint()

# Simulation of comparative RL Experiment
def SimulationRL(rho,rl):

    random.seed(RANDOM_SEED)
    mec = soCoM.MEC()
    mec.RHO = rho*mec.RHO
        
    print ("Envronment create!")
    env = simpy.Environment()
    print ("User create!") 
    for i in range(mec.USERS_NUM):
        user = soCoM.User(i)
        user.usersetting()
        user.usercreat()
        mec.USER_LIST.append(user)

    WAITING_LEN = simpy.Container(env,BUFFER, init=len(mec.WAITING_LIST))
    env.process(mec.runremote(env,WAITING_LEN))
    env.process(mec.refreshsys(env,WAITING_LEN,rl.name,'rho'+str(mec.RHO),1))
    env.process(mec.offloadDQ(env,WAITING_LEN,rl))
    env.process(mec.writelog(env,rl.name,'rho',int(mec.RHO)))
    env.run(until=SIM_TIME)
    mec.writeoffload(rl.name,'rho',int(mec.RHO))
    for u in mec.USER_LIST:
        u.userprint()


online = 'online'+str(soCoM.CD)+'_'
Simulation(RHO,online,'online')

offline = 'offline'+str(soCoM.CD)+'_'
Simulation(RHO,offline,'offline')

semi = 'semi'+str(soCoM.CD)+'_'
Simulation(RHO,semi,'semi')


##########RL##############
print("BEGIN training!")
rl = OFFLOADQ()
rl.mec.RHO = 4
rl.update(RANDOM_SEED)
rl.printCost()        
#####################################
SimulationRL(RHO,rl)
#tf.reset_default_graph()
