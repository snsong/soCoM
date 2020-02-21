# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 08:48:54 2019

@author: song

"""

"""
RL offloading training process

When using different DQN algorithms, different packages need to be imported.

"""

import soCoM
from RL_brainDQN import DeepQNetwork as DQN
#from RL_brainDouble import DoubleDQN as DQN
#from RL_brainDueling import DuelingDQN as DQN
#from RL_brainPrioritizedReplay import DQNPrioritizedReplay as DQN

import simpy
import random



USERS_NUM = soCoM.UN  

SIM_TIME = 10000
BUFFER = 500 
LEPI = 500 

class OFFLOADQ(object):
    def __init__(self):
       
        self.name = 'DQN'+str(soCoM.CD)+'_'+str(USERS_NUM)
        self.mec = soCoM.MEC()
        self.action_space = [str(i) for i in range(USERS_NUM)]
        self.n_actions = 2**USERS_NUM
        self.n_features = 6
        self.RL = DQN(self.n_actions, self.n_features,
                      learning_rate=0.01,
                      reward_decay=0.9,
                      e_greedy=0.9,
                      replace_target_iter=200,
                      memory_size=2000,
                      )
        
        self.done = True
        self.stepcount = 0
    
    def reset(self):
        self.mec.reset()  
        self.done = True
    def printCost(self):
        self.RL.plot_cost(self.name)
    def step(self, mec_, observation,env_, WAITING_LEN_):
        count = 0
        while True:
            count+=1
            if mec_.CHANNEL - mec_.CHANNEL_USED <= 1: 
                mec_.SCORE = -abs(mec_.SCORE)
                yield env_.timeout(mec_.TIMER*mec_.Delta*2)
                continue
            yield env_.timeout(mec_.TIMER*mec_.Delta)
            
            action = self.RL.choose_action(observation)
            userlist = mec_.randombin(action) 
            channel = mec_.CHANNEL-mec_.CHANNEL_USED
            for i in range(len(userlist)):
                if userlist[i] == 1:
                    userID = i
                    mec_.offloadOne(env_,userID,sum(userlist),channel)
            
            observation_ = mec_.getstate()
            reward = mec_.SCORE
            self.RL.store_transition(observation, action, reward, observation_)
            if (self.stepcount > 40) and (self.stepcount % 4 == 0):
                self.RL.learn()
            observation = observation_
    
    def update(self, RDSEED):
        self.reset()
        for episode in range(LEPI):
            self.reset()
            print ("learing episode %d" % (episode))
            random.seed(RDSEED)
            for i in range(USERS_NUM):
                user = soCoM.User(i)
                user.usersetting()
                user.usercreat()
                self.mec.USER_LIST.append(user)
            env_ = simpy.Environment()
            WAITING_LEN_ = simpy.Container(env_, BUFFER, init=len(self.mec.WAITING_LIST))
            
            observation = self.mec.getstate()
            env_.process(self.mec.runremote(env_,WAITING_LEN_))
            env_.process(self.mec.refreshsys(env_,WAITING_LEN_))
            env_.process(self.step(self.mec,observation,env_,WAITING_LEN_))
            env_.run(until=SIM_TIME)
            
            self.stepcount += 1
        self.setpcount = 0
        self.reset()
    
 
    
            
            


