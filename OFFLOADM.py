# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 08:48:54 2019

@author: song
"""

import soCoMM
#from RL_brainDQN import DeepQNetwork as DQN
#from RL_brainDouble import DoubleDQN as DQN
#from RL_brainDueling import DuelingDQN as DQN
from RL_brainPrioritizedReplay import DQNPrioritizedReplay as DQN
#from RL_brainPD import DQNPrioritizedReplay as DQN

import simpy
import random
import xlwt
import numpy as np


USERS_NUM = soCoMM.UN  
PEN = soCoMM.PEN
#NAME = 'DeepQ'
#NAME = 'DOU'
#NAME = 'DU'
NAME = 'PR'
SIM_TIME = 60000
BUFFER = 500 
LEPI = 50 

class OFFLOADQ(object):
    def __init__(self):
        self.name = NAME
        self.action_space = [str(i) for i in range(2)]
        self.n_actions = USERS_NUM #0-local，1-offload
        self.n_features = 6 # system state - getstate
        self.RL = DQN(self.n_actions, self.n_features,
                      learning_rate=0.01,
                      reward_decay=0.9,
                      e_greedy=0.9,
                      replace_target_iter=200,
                      memory_size=20000,
                      # output_graph=True
                      )
        self.done = True
        self.stepcount = 0
        
    
     ######RLlearning#############
    def reset(self):
        self.done = True
        self.stepcount = 0

    def printCost(self):
        self.RL.plot_cost(self.name)
        
    
    ######RLlearning#############
    def refreshstep(self,mec_,env_):
        while True:
            yield env_.timeout(mec_.TIMER)
            
            mec_.SYS_TIME = env_.now
            
            
            jobpool = []
            for Jr in mec_.JOB_POOL:
                userID = Jr[0]
                jobID = Jr[1]
                onejob = mec_.ul.USER_LIST[userID].JOB_LIST[jobID]
                
                if onejob.jobRunLeft > mec_.TIMER:
                    jobpool.append((userID,jobID))
                    mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft = mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft-mec_.TIMER
                else:
                    mec_.SYS_CPU -= (mec_.ul.USER_LIST[userID].jobCPU/mec_.RHO) 
                    mec_.ul.USER_LIST[userID].jobrefresh(env_,mec_.ul.USER_LIST[userID].JOB_LIST[jobID]) 
                    mec_.offloadJob.append(mec_.ul.USER_LIST[userID].JOB_LIST[jobID]) 
                    ########################################################################
                    mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge = env_.now - mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    mec_.Age += mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    mec_.Run += mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun 
                    mec_.commTime += mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobTT
                    mec_.Throughout += 1 
                    ###################################REWARD######################################
                    failrate = mec_.Failure/mec_.Throughout 
                    
                    score = mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun/mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobCEnergy
                    
                    if (mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge > mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun):
                        mec_.SCORE = -abs(score)*(1-failrate)
                        mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'FL'
                        mec_.Failure += 1
                    else:
                        mec_.SCORE = score*(1-failrate)
                        mec_.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'CP'  
                    mec_.REWARD += mec_.SCORE
                    
                    mec_.PRIORITY_LIST[userID] = mec_.ACTION
                    mec_.ul.USER_LIST[userID].userPriority[mec_.mecID] = mec_.ACTION
                    
                    
                    
                    #################################################################################
            mec_.JOB_POOL = jobpool
        
    
    
    
    def step(self, mec_,env_): 
        
        counter = 0
        while True:
            counter += 1
            yield env_.timeout(mec_.TIMER)
            
            if (mec_.CHANNEL - mec_.CHANNEL_USED <= 1) or (mec_.SYS_CPU > 0.9): 
                mec_.SCORE = -abs(mec_.SCORE)
                yield env_.timeout(mec_.TIMER*mec_.Delta)
                continue
            else:
                observation = mec_.getstate()
                mec_.ACTION  = self.RL.choose_action(observation) #
                if (counter < USERS_NUM *5) or (counter % 10 == 0):
                    pkey = random.sample([i for i in range(USERS_NUM)],k = mec_.ACTION)
                else:
                    plist = sorted(mec_.PRIORITY_LIST.items(),key = lambda i : i[1],reverse= 1)
                    pkey = [plist[i][0] for i in range(len(plist))][:mec_.ACTION]
                for i in range(len(pkey)):
                    userID = pkey[i]
                    mec_.offloadOne(env_,userID)
                observation_ = mec_.getstate()
                reward = mec_.SCORE
                self.RL.store_transition(observation, mec_.ACTION, reward, observation_)
                if (self.stepcount > 40) and (self.stepcount % 4 == 0):
                    self.RL.learn()
                observation = observation_
                self.stepcount += 1
        
    
                
    def update(self, RDSEED):
        
        self.reset()
        for episode in range(LEPI):
            self.reset()
            print ("qlearing episode %d setpcont %d" % (episode,self.stepcount))
            random.seed(RDSEED)
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
            env_ = simpy.Environment()
            
            #env_.process(ul.mobile(env_))#user mobile 
            
            WAITING_LEN0 = simpy.Container(env_,BUFFER, init=len(mec0.WAITING_LIST))
            env_.process(mec0.runremote(env_,WAITING_LEN0))
            env_.process(mec0.refreshtrans(env_,WAITING_LEN0))
            env_.process(mec0.refreshsys(env_,flag=0))
            env_.process(self.step(mec0,env_))
            # initial observation
            WAITING_LEN1 = simpy.Container(env_,BUFFER, init=len(mec1.WAITING_LIST))
            env_.process(mec1.runremote(env_,WAITING_LEN1))
            env_.process(mec1.refreshtrans(env_,WAITING_LEN1))
            env_.process(mec1.refreshsys(env_,flag=0))
            env_.process(self.step(mec1,env_))
            
            WAITING_LEN2 = simpy.Container(env_,BUFFER, init=len(mec2.WAITING_LIST))
            env_.process(mec2.runremote(env_,WAITING_LEN2))
            env_.process(mec2.refreshtrans(env_,WAITING_LEN2))
            env_.process(mec2.refreshsys(env_,flag=0))
            env_.process(self.step(mec2,env_))
            # initial observation
            WAITING_LEN3 = simpy.Container(env_,BUFFER, init=len(mec3.WAITING_LIST))
            env_.process(mec3.runremote(env_,WAITING_LEN3))
            env_.process(mec3.refreshtrans(env_,WAITING_LEN3))
            env_.process(mec3.refreshsys(env_,flag=0))
            env_.process(self.step(mec3,env_))
            # initial observation
            
            env_.run(until=SIM_TIME)
        self.reset()


 ######RLlearning fin#############
    
    
