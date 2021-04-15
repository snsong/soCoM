# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 15:09:31 2019

@author: song

soCoM simulation with multiple servers
"""

import soCoMM
from OFFLOADM import OFFLOADQ

import random
import simpy
import xlwt
import numpy as np
import tensorflow as tf


SIM_TIME = 150000
RANDOM_SEED = 40
RHO = 2
BUFFER = 500 #mec buffer 



def SimulationM(rho,ql,name):

    random.seed(RANDOM_SEED)
    ul = soCoMM.UL()
    for i in range(ul.USERS_NUM):
        user = soCoMM.User(i)
        user.usersetting()
        user.usercreat()
        ul.USER_LIST.append(user)
    
    mec0 = soCoMM.MEC(0,ul)
    mec0.setMEC(0,0,0,2,50)
    mec1 = soCoMM.MEC(1,ul)
    mec1.setMEC(1000,0,0,4,50)
    mec2 = soCoMM.MEC(2,ul)
    mec2.setMEC(0,1000,0,6,50)
    mec3 = soCoMM.MEC(3,ul)
    mec3.setMEC(1000,1000,0,8,50)
    
    name += str(mec0.USERS_NUM)
    print ("Envronment create!")
    env = simpy.Environment()
    print ("User create!")  

    WAITING_LEN0 = simpy.Container(env,BUFFER, init=len(mec0.WAITING_LIST))
    env.process(mec0.runremote(env,WAITING_LEN0))
    env.process(mec0.refreshtrans(env,WAITING_LEN0))
    env.process(mec0.refreshsys(env,name,'mec0'+str(mec0.RHO)+str(mec0.CHANNEL)))
    env.process(mec0.offloadDQ(env,WAITING_LEN0,ql))
    env.process(mec0.writelog(env,name,'mec0',str(mec0.RHO)+str(mec0.CHANNEL)))
    
    
    WAITING_LEN1 = simpy.Container(env,BUFFER, init=len(mec1.WAITING_LIST))
    env.process(mec1.runremote(env,WAITING_LEN1))
    env.process(mec1.refreshtrans(env,WAITING_LEN1))
    env.process(mec1.refreshsys(env,name,'mec1'+str(mec1.RHO)+str(mec1.CHANNEL)))
    env.process(mec1.offloadDQ(env,WAITING_LEN1,ql))
    env.process(mec1.writelog(env,name,'mec1',str(mec1.RHO)+str(mec1.CHANNEL)))
    
    WAITING_LEN2 = simpy.Container(env,BUFFER, init=len(mec2.WAITING_LIST))
    env.process(mec2.runremote(env,WAITING_LEN2))
    env.process(mec2.refreshtrans(env,WAITING_LEN2))
    env.process(mec2.refreshsys(env,name,'mec2'+str(mec2.RHO)+str(mec2.CHANNEL)))
    env.process(mec2.offloadDQ(env,WAITING_LEN2,ql))
    env.process(mec2.writelog(env,name,'mec2',str(mec2.RHO)+str(mec2.CHANNEL)))
    
    
    WAITING_LEN3 = simpy.Container(env,BUFFER, init=len(mec3.WAITING_LIST))
    env.process(mec3.runremote(env,WAITING_LEN3))
    env.process(mec3.refreshtrans(env,WAITING_LEN3))
    env.process(mec3.refreshsys(env, name,'mec3'+str(mec3.RHO)+str(mec3.CHANNEL)))
    env.process(mec3.offloadDQ(env,WAITING_LEN3,ql))
    env.process(mec3.writelog(env,name,'mec3',str(mec3.RHO)+str(mec3.CHANNEL)))
    

    env.run(until=SIM_TIME)
    
    mec0.writeoffload(name,'mec0',str(mec0.RHO)+str(mec0.CHANNEL))
    mec1.writeoffload(name,'mec1',str(mec1.RHO)+str(mec1.CHANNEL))
    mec2.writeoffload(name,'mec2',str(mec2.RHO)+str(mec2.CHANNEL))
    mec3.writeoffload(name,'mec3',str(mec3.RHO)+str(mec3.CHANNEL))
    #ul.drawtrace(name)
    for u in ul.USER_LIST:
        u.userprint()


##########Rl training##############
print("BEGIN RL Learning!")
ql = OFFLOADQ()
ql.update(RANDOM_SEED)
#ql.update_offline(RANDOM_SEED)
#ql.printCost()        
#####################################

    

SimulationM(RHO,ql,ql.name)
tf.reset_default_graph()
