# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 08:40:16 2019

@author: song

"""
"""
soCoM system model, which is consist of job, user and mec server.

Simulation based on SimPy:  https://simpy.readthedocs.io/en/latest/
SimPy is a process-based discrete-event simulation framework based on standard Python.

"""

import random
import numpy as np

random.seed(40)


UN = 5 #Numbers of user equipment
CD = 2 #channel bandwidth allocation factor

class Job(object):
    def __init__(self, userID, jobID):
        ######base info##########
        self.userID = userID 
        self.jobID = jobID 
        self.jobTran = 0.0 
        self.jobDTran = 0.0 
        self.jobRun = 0.0 
        self.jobCPU = 0.0 
        self.jobCEnergy = 0.0 
        self.jobLEnergy = 0.0 
        self.jobType = 'normal' 
        self.jobState = 'LW' #=act,inh,lw,lr,ts,rw,rr,cp,fl
        #############online changing#########
        self.jobRunLeft = 0.0 
        self.jobTransLeft = 0.0 
        self.jobChannel = 0.0 
        ###########log#################
        self.jobBegin = 0.0 
        self.jobFinish = 0.0 
        self.jobOffload = 0.0 
        self.jobRT =0.0
        self.jobTT = 0.0
        self.jobAge = 0.0 
   

class User(object):
    def __init__(self, userID):
        self.userID = userID
        self.JOB_LIST = [] 
        self.jobData = 0.0 
        self.jobTrans = [20] 
        self.jobRuns = [20] 
        self.jobCPU = 0.1 
        self.jobNums = 50 
        self.jobCEnergy = [20] 
        self.jobLEnergy = [20] 
        ###############log###########
        self.Throughout = 0.0 
        self.CEnergy = 0.0 
        self.LEnergy = 0.0 
        self.commTotal = 0.0
        self.Age = 0.0 
       
    
     ##############################################################
     
    def usersetting(self):
        self.jobNums = 10
        self.jobData = (UN-self.userID)*64
        self.jobRuns = [(self.userID+1)*25*i for i in range(1,5)]
        self.jobCPU = 0.1
        self.jobLEnergy = [(self.userID+1)*1.25*i for i in range(7,25)]
        

    def setjobenergy(self,jid,jobtran):
        BDu = self.JOB_LIST[jid].jobChannel
        BDd = BDu/2
        self.JOB_LIST[jid].jobTran = self.jobData/BDu 
        self.JOB_LIST[jid].jobDTran = self.jobData/BDd  
        LET = BDu*0.438 + 0.051*BDd + 1.288
        #WIFI = BDu*0.283 + 0.137*BDd + 0.132
        #self.JOB_LIST[jid].jobCEnergy = random.choice([LET,WIFI])*(jobtran/1000)
        self.JOB_LIST[jid].jobCEnergy = LET*(jobtran/1000)
        
        
       
    def jobcreat(self,jobid,jobtype='normal'):
        jobrun = random.choice(self.jobRuns)
        onejob = Job(self.userID, jobid)
        onejob.jobRun = jobrun
        onejob.jobType = jobtype
        onejob.jobCPU = self.jobCPU
        onejob.jobLEnergy = random.choice(self.jobLEnergy)
        
        return onejob
    
    def usercreat(self):
        
        onejob = self.jobcreat(0)
        self.JOB_LIST.append(onejob)
        
        for i in range(1,self.jobNums):
            onejob = self.jobcreat(i)
            self.JOB_LIST.append(onejob)
            
    
    def userprint(self):
        print("User %d totalfinish %.2f, energy %.2f , age %.2f." % (self.userID, self.Throughout, self.CEnergy, self.Age))
    
    def usersend(self):
        jobid = -1
        for i in range(len(self.JOB_LIST)):
            job = self.JOB_LIST[i]
            if  job.jobState == 'LW':
                jobid = i
                self.jobappend()
                return jobid
        if jobid == -1:
            self.jobappend()
            job = self.JOB_LIST[-1]
        return jobid
    
    def userrun(self):
        jobid = -1
        for i in range(len(self.JOB_LIST)):
            job = self.JOB_LIST[i]
            if  job.jobState == 'LW':
                jobid = i
                return jobid
        return jobid
    
    def jobrefresh(self,env, fjob):
        jobID = fjob.jobID
        self.Throughout += 1
        self.JOB_LIST[jobID].jobFinish= env.now
    
    def jobappend(self):
        jid = len(self.JOB_LIST)
        onejob = self.jobcreat(jid)
        self.JOB_LIST.append(onejob)
        
    def runlocal(self,env): 
        while True:
            jobID = self.userrun()
            if jobID == -1:
                self.jobappend()
                continue
            else:
                self.JOB_LIST[jobID].jobState = 'LR' 
                self.JOB_LIST[jobID].jobBegin = env.now
                RUNNINGTIME = self.JOB_LIST[jobID].jobRun
                yield env.timeout(RUNNINGTIME)
                self.JOB_LIST[jobID].jobState = 'CP' 
                self.LEnergy += self.JOB_LIST[jobID].jobLEnergy
                self.jobrefresh(env,self.JOB_LIST[jobID])
                self.jobappend()
    

class MEC(object):
    def __init__(self):
        ##########basic info##########
        self.USERS_NUM = UN
        self.USER_LIST = [] 
        self.CHANNEL = 50.0
        self.RHO = 2.0 
        self.TIMER = 10 
        self.Delta = UN 
        self.CD = CD
        ##########online changing#######
        self.JOB_POOL = [] 
        self.TRANS_POOL = [] 
        self.WAITING_LIST = []  
        self.CHANNEL_USED = 0.0 
        self.SYS_TIME = 0.0 
        self.SYS_CPU = 0.0 
        self.ACTION = 0 
        self.SCORE = 0.0 
        ####################log################
        self.offloadJob = [] 
        self.Age = 0.0
        self.commTime = 0.0
        self.commEnergy = 0.0
        self.Run = 0.0
        #################RL###################
        self.REWARD = 0.0 
 

    ###############################system log###################################################      
    def writelog(self,env,fn, name, value, timeslot = 5000):
        yield env.timeout(5000)
        f = open('.\\data\\USER_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','w')
        oneline = 'TIMESLOT \t Throughout \t Age \t Run \t commTotal \t commEnergy \t reward\n'
        f.write(oneline)
        f.close()
        while True:
            yield env.timeout(timeslot)
            age = 0.0
            run = 0.0
            throu = 0.0
            comm = 0.0
            energy = 0.0
            sumreward = self.REWARD
            ucout = len(self.USER_LIST)
            for u in self.USER_LIST:
                throu += float(u.Throughout)
            age = self.Age/ucout/1000
            run = self.Run/ucout
            throu = throu/ucout
            comm = self.commTime/ucout/1000
            energy = self.commEnergy/ucout
            sumreward = self.REWARD
            f = open('.\\data\\USER_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','a')
            oneline = str(env.now/1000)+'\t'+str(throu)+'\t'+str(age)+'\t'+str(run)+'\t'+str(comm)+'\t'+str(energy)+'\t'+str(sumreward)+'\n'
            f.write(oneline)
        f.close()
    
    def writeoffload(self,fn, name, value):
        f = open('.\\data\\JOB_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','w')
        titleline = 'No \t Uid \t Jid  \t offloadtime \t begintime \t commutime \t runtime \t energy \t AoI\n'
        f.write(titleline)
        i = 0
        for j in self.offloadJob:
            oneline = str(i) +'\t'+ str(j.userID) +'\t'+ str(j.jobID) +'\t'+str(j.jobOffload/1000) +'\t'+ str(j.jobBegin/1000) +'\t'
            oneline += str(j.jobTran/1000) +'\t'+ str(j.jobRun/1000) +'\t'+ str(j.jobCEnergy) +'\t'+ str(j.jobAge/1000) +'\n'
            i +=1
            f.write(oneline)
        f.close()
      
    ######RL#############
    def getstate(self): 
        state = []
        state.append(self.CHANNEL_USED)
        state.append(self.SYS_CPU)
        state.append(len(self.JOB_POOL))
        state.append(len(self.TRANS_POOL))
        
        uwait = 0.0
        utran = 0.0
        for i in self.JOB_POOL:
            uwait += self.USER_LIST[i[0]].JOB_LIST[i[1]].jobRunLeft
        for j in self.TRANS_POOL:
            utran += self.USER_LIST[j[0]].JOB_LIST[j[1]].jobTransLeft
        state.append(uwait)
        state.append(utran)
        state = np.array(state)
        return state
    
    def reset(self):
        self.USER_LIST = [] 
        
        self.JOB_POOL = [] 
        self.TRANS_POOL = [] 
        self.WAITING_LIST = []  
        self.CHANNEL_USED = 0.0 
        self.SYS_TIME = 0.0 
        self.SYS_CPU = 0.0 
       
        self.offloadJob = [] 
        self.REWARD = 0.0    
    ######RL#############
  
    #####################################
    def channeldisturb(self, userID,jobID,jobnum,channel):
        disturb = np.log2(1+1/(self.CD+jobnum))
        cl = channel*disturb
        
        if self.CHANNEL_USED+cl > self.CHANNEL:
            return -1
        self.CHANNEL_USED += cl
        jt = self.USER_LIST[userID].jobData/cl
        self.USER_LIST[userID].JOB_LIST[jobID].jobChannel = cl
        return jt
    ###################################################
    
    
    def offloadOne(self,env,userID,jobnum,channel):
        jobID = self.USER_LIST[userID].usersend()
        if jobID == -1:
            return
        
        TRANSPOTTIME = self.channeldisturb(userID,jobID,jobnum,channel)
        if TRANSPOTTIME == -1:
            self.SCORE = -abs(self.SCORE)
            return
        
        self.USER_LIST[userID].JOB_LIST[jobID].jobOffload = env.now       
        self.USER_LIST[userID].JOB_LIST[jobID].jobState = 'TS' 
        self.USER_LIST[userID].JOB_LIST[jobID].jobAge = env.now 
        self.USER_LIST[userID].JOB_LIST[jobID].jobTT = TRANSPOTTIME 
        self.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft = TRANSPOTTIME
        self.USER_LIST[userID].setjobenergy(jobID,TRANSPOTTIME) 
        self.commEnergy += self.USER_LIST[userID].JOB_LIST[jobID].jobCEnergy 
        self.TRANS_POOL.append((userID,jobID)) 
        
    def runremote(self,env, WAITING_LEN):
        while True:
            yield env.timeout(self.TIMER)

            if self.SYS_CPU > 0.8: 
                yield env.timeout(self.TIMER*2)
                self.SCORE = -abs(self.SCORE)
                continue
            else:
                yield WAITING_LEN.get(1) 
                job = self.WAITING_LIST.pop(0)
                userID = job.userID
                jobID = job.jobID
                self.JOB_POOL.append((userID,jobID)) 
                self.SYS_CPU += self.USER_LIST[userID].JOB_LIST[jobID].jobCPU
                #######################################################################################
                self.USER_LIST[userID].JOB_LIST[jobID].jobState = 'RR' 
                self.USER_LIST[userID].JOB_LIST[jobID].jobBegin = env.now
                RUNNINGTIME = float(self.USER_LIST[userID].JOB_LIST[jobID].jobRun)/self.RHO
                self.USER_LIST[userID].JOB_LIST[jobID].jobRT = RUNNINGTIME
                self.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft = RUNNINGTIME
            
        
    def refreshsys(self,env,WAITING_LEN,name='',value='',flag = 0):
        if flag ==1:
            f = open('.\\data\\ACTION_'+str(name)+'_'+str(value)+'.data','w')
            oneline = 'sysTime \t'+'ACTION \t'+'ChannelUsed \t'+'TransJob \t'+'CPU \t'+'RunningJob \t'+'ActionQos \n'
            f.write(oneline)
            f.close()
        while True:
            yield env.timeout(self.TIMER)
            TIMER = env.now - self.SYS_TIME
            self.SYS_TIME = env.now
            if flag ==1:
                f = open('.\\data\\ACTION_'+str(name)+'_'+str(value)+'.data','a')
                oneline = str(self.SYS_TIME)+'\t' +str(self.ACTION)+'\t' +str(self.CHANNEL_USED)+ '\t' + str(len(self.TRANS_POOL)) + '\t' +str(self.SYS_CPU)+ '\t' + str(len(self.JOB_POOL))
                oneline += '\t' +str(self.SCORE) + '\n'
                f.write(oneline)
            
            transpool = []
            for Jt in self.TRANS_POOL:
                userID = Jt[0]
                jobID = Jt[1]
                onejob = self.USER_LIST[userID].JOB_LIST[jobID]
                if onejob.jobTransLeft > TIMER:
                    transpool.append((userID,jobID))
                    self.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft = self.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft-TIMER
                else:
                    self.USER_LIST[userID].JOB_LIST[jobID].jobState = 'RW'  
                    self.CHANNEL_USED -= self.USER_LIST[userID].JOB_LIST[jobID].jobChannel
                    self.WAITING_LIST.append(self.USER_LIST[userID].JOB_LIST[jobID])
                    self.USER_LIST[userID].jobappend()
                    yield WAITING_LEN.put(1)
            self.TRANS_POOL = transpool
            
            
            jobpool = []
            for Jr in self.JOB_POOL:
                userID = Jr[0]
                jobID = Jr[1]
                onejob = self.USER_LIST[userID].JOB_LIST[jobID]
                if onejob.jobRunLeft > TIMER:
                    jobpool.append((userID,jobID))
                    self.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft = self.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft-TIMER
                else:
                    self.USER_LIST[userID].JOB_LIST[jobID].jobState = 'CP'  
                    self.SYS_CPU -= self.USER_LIST[userID].JOB_LIST[jobID].jobCPU
                    self.USER_LIST[userID].jobrefresh(env,self.USER_LIST[userID].JOB_LIST[jobID])
                    self.offloadJob.append(self.USER_LIST[userID].JOB_LIST[jobID])
                    ########################################################################
                    self.USER_LIST[userID].JOB_LIST[jobID].jobAge = env.now - self.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    self.Age += self.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    self.Run += self.USER_LIST[userID].JOB_LIST[jobID].jobRun
                    self.commTime += self.USER_LIST[userID].JOB_LIST[jobID].jobTT
                    ###################################REWARD######################################
                    self.SCORE = self.USER_LIST[userID].JOB_LIST[jobID].jobRun/self.USER_LIST[userID].JOB_LIST[jobID].jobCEnergy
                    self.REWARD += self.SCORE
                    #################################################################################
            self.JOB_POOL = jobpool
        f.close()
    
  
    
    def offline(self):
        score = 0.0
        action = 1
        for i in range(2**self.USERS_NUM):
            userlist = self.randombin(i)
            score_ = 0
            jobnum = sum(userlist)
            channel = self.CHANNEL-self.CHANNEL_USED
            cl = 0
            for u in range(len(userlist)):
                if userlist[u] == 1:
                    userID = u
                    disturb = np.log2(1+1/(self.CD+jobnum))
                    cl = channel*disturb
                    score_ += np.average(self.USER_LIST[userID].jobRuns)/self.USER_LIST[userID].jobData*cl
            if score_ > score:
                score = score_
                action = i
        return action
    
    def spac(self):
        score = 100000.0
        action = 1
        for i in range(2**self.USERS_NUM):
            userlist = self.randombin(i)
            score_ = 100000.0
            jobnum = sum(userlist)
            channel = self.CHANNEL-self.CHANNEL_USED
            cl = 0
            for u in range(len(userlist)):
                if userlist[u] == 1:
                    userID = u
                    disturb = np.log2(1+1/(self.CD+jobnum))
                    cl = channel*disturb
                    if cl < 1:
                        score_ = 100000.0
                    else:
                        score_ += self.USER_LIST[userID].jobData/cl
            if score_ < score:
                score = score_
                action = i
        return action
            
    def randombin(self,action):
        userlist = list(bin(action).replace('0b',''))
        zeros = self.USERS_NUM - len(userlist)
        ll = [0 for i in range(zeros)]
        for i in userlist:
            ll.append(int(i))
        return ll
    #################################offloading strategy########################################
    #online
    def offloadOL(self,env, WAITING_LEN):
        while True:
            if self.CHANNEL - self.CHANNEL_USED <= 1: 
                self.SCORE = -abs(self.SCORE)
                yield env.timeout(self.TIMER*self.Delta*2)
                continue
            yield env.timeout(self.TIMER*self.Delta)
            self.ACTION = random.randint(1,2**self.USERS_NUM-1)
            userlist = self.randombin(self.ACTION) 
            jobnum = sum(userlist)
            channel = self.CHANNEL-self.CHANNEL_USED
            for i in range(len(userlist)):
                if userlist[i] == 1:
                    userID = i
                    self.offloadOne(env,userID,jobnum,channel)
    #offline
    def offloadOF(self,env, WAITING_LEN):
        while True:
            if self.CHANNEL - self.CHANNEL_USED <= 1: 
                self.SCORE = -abs(self.SCORE)
                yield env.timeout(self.TIMER*self.Delta*2)
                continue
            yield env.timeout(self.TIMER*self.Delta)
            self.ACTION = self.offline() 
            userlist = self.randombin(self.ACTION) 
            jobnum = sum(userlist)
            channel = self.CHANNEL-self.CHANNEL_USED
            for i in range(len(userlist)):
                if userlist[i] == 1:
                    userID = i
                    self.offloadOne(env,userID,jobnum,channel)
    #semi-online
    def offloadSe(self,env, WAITING_LEN):
        while True:
            if self.CHANNEL - self.CHANNEL_USED <= 1: 
                self.SCORE = -abs(self.SCORE)
                yield env.timeout(self.TIMER*self.Delta*2)
                continue
            yield env.timeout(self.TIMER*self.Delta)
            self.ACTION = 1 
            userlist = self.randombin(self.ACTION) 
            jobnum = sum(userlist)
            channel = self.CHANNEL-self.CHANNEL_USED
            for i in range(len(userlist)):
                if userlist[i] == 1:
                    userID = i
                    self.offloadOne(env,userID,jobnum,channel)
    #RL               
    def offloadDQ(self, env,WAITING_LEN,ql):
        while True:
            observation = self.getstate()
            if self.CHANNEL - self.CHANNEL_USED <= 1: 
                self.SCORE = -abs(self.SCORE)
                yield env.timeout(self.TIMER*self.Delta*2)
                continue
            yield env.timeout(self.TIMER*self.Delta)
            self.ACTION = ql.RL.choose_action(observation)
            userlist = self.randombin(self.ACTION) 
            channel = self.CHANNEL-self.CHANNEL_USED
            for i in range(len(userlist)):
                if userlist[i] == 1:
                    userID = i
                    self.offloadOne(env,userID,sum(userlist),channel)
    
                    
            