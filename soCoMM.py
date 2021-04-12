# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 08:40:16 2019

@author: song
"""
"""
soCoM system model with multiple servers, which is consist of job, user and mec server.

Simulation based on SimPy:  https://simpy.readthedocs.io/en/latest/
SimPy is a process-based discrete-event simulation framework based on standard Python.

"""

import random
import numpy as np
import matplotlib.pyplot as plt

random.seed(40)

#As the number of users increases, the frequency of unloading must be reduced, otherwise it will be blocked
UN = 100
CD = 5
PEN = 1
PLIST = 10

class Job(object):
    def __init__(self, userID, jobID):
        ######basic info##########
        self.userID = userID #user ID
        self.jobID = jobID #task ID 
        self.jobTran = 0.0 #upload time
        self.jobDTran = 0.0 #down load time 
        self.jobRun = 0.0 #local processing time 
        self.jobCPU = 0.0 #CPU and resource occurpy
        self.jobCEnergy = 0.0 #Transmission energy consumption
        self.jobLEnergy = 0.0 #Local execution energy consumption
        self.jobType = 'normal' #Task type
        self.jobState = 'LW' #Activation=act, printing=inh, local waiting=lw, local execution=lr, transmission=ts, remote waiting=rw, remote execution=rr, completion=cp, failure=fl
        self.jobValue = 1.0 #Task value
        #############Dynamic changes during execution#########
        self.jobRunLeft = 0.0 #Task remote execution time remaining
        self.jobTransLeft = 0.0 #Task transfer time remaining
        self.jobChannel = 0.0 #The obtained channel bandwidth uses Mbps
        ###########Execution completed record#################
        self.jobBegin = 0.0 #The time when the task started
        self.jobFinish = 0.0 #The time when the task execution ends
        self.jobOffload = 0.0 #The time when the task started to unload
        self.jobRT =0.0#Execution time
        self.jobTT = 0.0#Transmission time
        self.jobAge = 0.0 #Age = the time from the start of the offloading to the end of the execution
   

class User(object):
    def __init__(self, userID):
        self.userID = userID
        self.JOB_LIST = [] #User task list
        self.jobData = 0.0 #Task transfer data volume
        self.jobTrans = [20] #Task transmission time-distribution-
        self.jobRuns = 20 #Task local execution time-distribution-
        self.jobCPU = 0.1 #Task CPU utilization
        self.jobNums = 50 #Initial number of tasks
        self.jobCEnergy = [20] #Transmission energy consumption
        self.jobLEnergy = [20]
        self.jobDDL = 10 #Task deadline
        
        ###############location information#################
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.speed = 0.0
        self.vector = [1,0] #Motion direction vector (x, y)
        self.trace = [] #User movement trajectory
        self.round = []
        self.userPriority = [0,0,0,0] #User priority
        self.userMEC = [0,0,0,0] #User and mec connectivity
        ###############Log###########
        self.Throughout = 0.0 #Throughput
        self.CEnergy = 0.0 #Remote energy consumption
        self.LEnergy = 0.0 #Local energy consumption
        self.commTotal = 0.0#When the transfer occurred
        self.Age = 0.0 #User task age
       
    
     ##############################################################
     
    def usersetting(self):
        self.jobNums = 10
        self.jobData = (UN-self.userID)*8 #Decreasing data volume, kb
        self.jobRuns = (self.userID+1)*10 #Increasing calculation time
        self.jobDDL = (self.userID+1)*10
       
        self.jobCPU = random.randint(1,UN)/(UN*2) #Increasing resource usage
        self.jobLEnergy = [(self.userID+1)*1.25*i for i in range(7,25)]
        self.X = 500
        self.Y = 500
        self.round = [self.X,self.Y]
        self.trace=[[self.X],[self.Y]]
        self.speed = random.choice([10,20,15])#speed，m/s
        self.vector = random.choice([[1,0],[0,1],[-1,0],[0,-1]])
        

    def setjobenergy(self,jid,jobtran):
        BDu = self.JOB_LIST[jid].jobChannel
        BDd = BDu/2
        self.JOB_LIST[jid].jobTran = self.jobData/BDu #Sampling from the transmission time distribution
        self.JOB_LIST[jid].jobDTran = self.jobData/BDd  
        LET = BDu*0.438 + 0.051*BDd + 1.288 #4G
        #WIFI = BDu*0.283 + 0.137*BDd + 0.132
        #self.JOB_LIST[jid].jobCEnergy = random.choice([LET,WIFI])*(jobtran/1000)
        self.JOB_LIST[jid].jobCEnergy = LET*(jobtran/1000)
        
        
       
    def jobcreat(self,jobid,jobtype='normal'):
        jobrun = self.jobRuns #Sampling from the execution time distribution
        onejob = Job(self.userID, jobid)
        onejob.jobRun = jobrun
        onejob.jobValue = jobrun
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
    
    def usersend(self,x,y,mecid):# User offloading algorithm
        jobid = -1
        distance = (self.X -x)**2 +(self.Y -y)**2
        
        if distance > 1e6: #Not in range
            self.userMEC[mecid] = 0
            return -1
        else:
            self.userMEC[mecid] = 1
        
        if (sum(self.userMEC)>=2) & (self.userPriority[mecid] < max(self.userPriority)): #Multiple connection choices and not optimal
            return -1
        for i in range(len(self.JOB_LIST)):
            job = self.JOB_LIST[i]
            
            if  job.jobState == 'LW':
                jobid = i
                self.jobappend() #Ensure that there is a continuous task flow
                return jobid
        return jobid
    
    def userrun(self):# Local execution of the most expensive tasks
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
                
                self.JOB_LIST[jobID].jobState = 'LR' #Local execution
                self.JOB_LIST[jobID].jobBegin = env.now
                RUNNINGTIME = self.JOB_LIST[jobID].jobRun
                
                yield env.timeout(RUNNINGTIME)
                self.JOB_LIST[jobID].jobState = 'CP'  #Finished
                self.LEnergy += self.JOB_LIST[jobID].jobLEnergy
                
                self.jobrefresh(env,self.JOB_LIST[jobID])
                self.jobappend()

class UL(object): #Total control of the movement of all users
    def __init__(self):
        self.USERS_NUM = UN
        self.USER_LIST = [] #user list
        self.frequncy = 100.0 
        
    
    def reset(self):
        self.USER_LIST = [] 
    
    def M_strait(self,userID): #Linear moving model
        userspeed = self.USER_LIST[userID].speed*self.frequncy/1000
        flag = [self.USER_LIST[userID].vector[0],self.USER_LIST[userID].vector[1]] #Current direction of travel
        reflag = [-flag[0],-flag[1]] #负方向，禁止掉头
        if (abs(self.USER_LIST[userID].X-self.USER_LIST[userID].round[0])<5) & (abs(self.USER_LIST[userID].Y-self.USER_LIST[userID].round[1])<5):
            self.USER_LIST[userID].X += (userspeed*self.USER_LIST[userID].vector[0])
            self.USER_LIST[userID].Y += (userspeed*self.USER_LIST[userID].vector[1])
        elif (abs(self.USER_LIST[userID].X-500)<2) & (abs(self.USER_LIST[userID].Y-500)<2):#-1(500,500)
            #print('0',flag)
            ll = [[1,0],[0,1],[-1,0],[0,-1]]
            ll.remove(reflag)#Turn around and remove
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 500
            self.USER_LIST[userID].Y = 500
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-0)<2) & (abs(self.USER_LIST[userID].Y-0)<2):
            #print('1',flag)
            ll = [[1,0],[0,1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 0
            self.USER_LIST[userID].Y = 0
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-500)<2) & (abs(self.USER_LIST[userID].Y-0)<2):
            #print('2',flag)
            ll = [[1,0],[0,1],[-1,0]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 500
            self.USER_LIST[userID].Y = 0
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-1000)<2) & (abs(self.USER_LIST[userID].Y-0)<2):
            #print('3',flag)
            ll = [[0,1],[-1,0]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 1000
            self.USER_LIST[userID].Y = 0
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-1000)<2) & (abs(self.USER_LIST[userID].Y-500)<2):
            #print('4',flag)
            ll = [[0,1],[-1,0],[0,-1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 1000
            self.USER_LIST[userID].Y = 500
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-1000)<2) & (abs(self.USER_LIST[userID].Y-1000)<2):
            #print('5',flag)
            ll = [[-1,0],[0,-1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 1000
            self.USER_LIST[userID].Y = 1000
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-500)<2) & (abs(self.USER_LIST[userID].Y-1000)<2):
            #print('6',flag)
            ll = [[1,0],[-1,0],[0,-1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 500
            self.USER_LIST[userID].Y = 1000
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-0)<2) & (abs(self.USER_LIST[userID].Y-1000)<2):
            #print('7',flag)
            ll = [[1,0],[0,-1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 0
            self.USER_LIST[userID].Y = 1000
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        elif (abs(self.USER_LIST[userID].X-0)<2) & (abs(self.USER_LIST[userID].Y-500)<2):
            #print('8',flag,self.USER_LIST[userID].round)
            ll = [[1,0],[0,-1],[0,1]]
            ll.remove(reflag)
            flag = random.choice(ll)
            self.USER_LIST[userID].X = 0
            self.USER_LIST[userID].Y = 500
            self.USER_LIST[userID].round = [self.USER_LIST[userID].X,self.USER_LIST[userID].Y]
        self.USER_LIST[userID].vector[0] = flag[0]
        self.USER_LIST[userID].vector[1] = flag[1]
        self.USER_LIST[userID].X += (userspeed*self.USER_LIST[userID].vector[0])
        self.USER_LIST[userID].Y += (userspeed*self.USER_LIST[userID].vector[1])
        self.USER_LIST[userID].trace[0].append(self.USER_LIST[userID].X)
        self.USER_LIST[userID].trace[1].append(self.USER_LIST[userID].Y)
    
    
    def mobile(self,env): #userrun is stratege functionname
        while True:
            yield env.timeout(self.frequncy)
            for u in self.USER_LIST:
                self.M_strait(u.userID)
                
    def drawtrace(self,name):
        fig=plt.figure(figsize=(15,6))
        plt.rcParams.update({'font.size': 6})
        plt.title("User Choice")
        for uid in range(len(self.USER_LIST)):
            u = self.USER_LIST[uid]
            ax = plt.subplot(2,5,uid+1)
            
            ax.scatter(u.trace[0], u.trace[1], c='b',alpha=0.1)
            ax.scatter(u.trace[0][0],u.trace[1][0],c='r')#Red is the starting point
            ax.scatter(u.trace[0][-1],u.trace[1][-1],c='g')#Green is the end
            ax.set_xlabel('USER'+str(uid))
            plt.xlim(-10, 1010)
            plt.ylim(-10, 1010)
        plt.savefig('.\\data\\movetrace'+name+'.svg',format='svg',dpi=500,bbox_inches='tight') 
        plt.savefig('.\\data\\movetrace'+name+'.png',format='png',dpi=500,bbox_inches='tight') 



class MEC(object):
    def __init__(self,mecid,userlist):
        ##########Basic Information##########
        self.mecID = mecid
        self.USERS_NUM = UN
        self.ul = userlist
        self.CHANNEL = 50.0#Mps, KBpms total bandwidth
        self.RHO = 2.0 #Local and remote execution basic rate ratio ρ
        self.TIMER = 10 #System status refresh frequency
        self.Delta = 5 #Offloading frequency=TIMER*Delta
        self.CD = CD #Bandwidth allocation method
        
        self.mecX = 0.0 #mec location information
        self.mecY = 0.0
        self.mecZ = 0.0
        
        ##########Real-time change information#######
        self.JOB_POOL = [] #Task list in progress
        self.TRANS_POOL = [] #Transferring task list
        self.WAITING_LIST = []  #Remote waiting list
        self.PRIORITY_LIST = {}  #Priority list
        self.CHANNEL_USED = 0.0 #Channel occupied bandwidth
        self.SYS_TIME = 0.0 #System last time
        self.SYS_CPU = 0.0 #The current CPU usage of the system
        self.ACTION = 0 #The last action taken by the system
        self.SCORE = 0.0 #System last score
        ####################log################
        self.offloadJob = [] #Task records that have been offloaded
        self.Age = 0.0 #Total age
        self.commTime = 0.0 #Total transmission time
        self.commEnergy = 0.0 #Total transmission energy consumption
        self.Run = 0.0 #Total execution time
        self.Throughout = 1 #Total offloading completed tasks
        self.Failure = 1 #
        #################RL###################
        self.REWARD = 0.0 #
    
    def setMEC(self,x,y,z,rho,channel):
        self.mecX = x #mec location information
        self.mecY = y
        self.mecZ = z
        self.RHO = rho #Computing speed
        self.CHANNEL = channel #Bandwidth, network resources
        for u in self.ul.USER_LIST:
            self.PRIORITY_LIST[u.userID]=u.userPriority[self.mecID]
        #print(self.PRIORITY_LIST)

#####################################System log###################################################      
    def writelog(self,env,fn, name, value, timeslot = 10000):
        yield env.timeout(5000)
        f = open('.\\data\\USER_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','w')
        oneline = 'TIMESLOT \t Throughout \t Failure \t Failurerate \t User \t Age \t Run \t commTotal \t commEnergy \t reward\n'
        f.write(oneline)
        f.close()
        while True:
            yield env.timeout(timeslot)
            age = 0.0
            run = 0.0
            throu = 0.0
            comm = 0.0
            energy = 0.0
            user = 0
            
            for i in range(self.USERS_NUM):
                user += self.ul.USER_LIST[i].userMEC[self.mecID]
            
            sumreward = self.REWARD
            
            throu = self.Throughout
            fail = self.Failure
            age = self.Age/1000
            run = self.Run
            comm = self.commTime/1000
            energy = self.commEnergy
            sumreward = self.REWARD
            f = open('.\\data\\USER_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','a')
            oneline = str(env.now/1000)+'\t'+str(throu)+'\t'+str(fail)+'\t'+str(fail/throu)+'\t'+str(user)+'\t'+str(age)+'\t'+str(run)+'\t'+str(comm)+'\t'+str(energy)+'\t'+str(sumreward)+'\n'
            f.write(oneline)
        f.close()
    
    def writeoffload(self,fn, name, value):
        f = open('.\\data\\JOB_'+str(fn)+'_'+str(name)+'_'+str(value)+'.data','w')
        titleline = 'No \t Uid \t Jid  \t offloadtime \t commutime \t runtime \t energy \t AoI \t state\n'
        f.write(titleline)
        i = 0
        for j in self.offloadJob:
            oneline = str(i) +'\t'+ str(j.userID) +'\t'+ str(j.jobID) +'\t'+str(j.jobOffload/1000) +'\t'
            oneline += str(j.jobTran/1000) +'\t'+ str(j.jobRun/1000) +'\t'+ str(j.jobCEnergy) +'\t'+ str(j.jobAge/1000) +'\t'+str(j.jobState)+'\n'
            i +=1
            f.write(oneline)
        f.close()
      
    ######RLlearning#############
    def getstate(self): #system status
        state = []
        state.append(self.CHANNEL_USED)
        state.append(self.SYS_CPU)
        state.append(len(self.JOB_POOL))
        state.append(len(self.TRANS_POOL))
        
        uwait = 0.0
        utran = 0.0
        for i in self.JOB_POOL:
            uwait += self.ul.USER_LIST[i[0]].JOB_LIST[i[1]].jobRunLeft
        for j in self.TRANS_POOL:
            utran += self.ul.USER_LIST[j[0]].JOB_LIST[j[1]].jobTransLeft
        state.append(uwait)
        state.append(utran)
        state = np.array(state)
        
        
        return state
    
    def reset(self):
        
        ##########Real-time change information#######
        self.JOB_POOL = [] #Task list in progress
        self.TRANS_POOL = [] #Transferring task list
        self.WAITING_LIST = []  #Remote waiting list
        self.CHANNEL_USED = 0.0 #Channel occupied bandwidth
        self.SYS_TIME = 0.0 #System last time
        self.SYS_CPU = 0.0 #The current CPU usage of the system
        ####################log################
        self.offloadJob = [] #Task records that have been uninstalled
        self.REWARD = 0.0    
    ######RLlearning#############
    
    
    
        
    
    #####Channel interference################################
    def channeldisturb(self, userID,jobID):#Bandwidth allocation
        cl = self.CHANNEL-self.CHANNEL_USED
        
        cl = cl/self.CD
        self.CHANNEL_USED += cl
        jt = self.ul.USER_LIST[userID].jobData/cl
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobChannel = cl
        
        return jt
    ###################################################
    
    
    def offloadOne(self,env,userID): #offload a task
        jobID = self.ul.USER_LIST[userID].usersend(self.mecX,self.mecY,self.mecID)
        if jobID == -1:
            #print('OFFLOAD: U%dJ%d is no job sent at %.2f' % (userID,jobID,env.now))
            return
        
        TRANSPOTTIME = self.channeldisturb(userID,jobID)#Really required transmission time
        
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobOffload = env.now  #Task start transmission time  
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'TS'  #Task status changes, start transmission
                ######
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge = env.now #Record birthday moments
                #######
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobTT = TRANSPOTTIME #Task real transmission time record
        self.ul.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft = TRANSPOTTIME#Remaining transmission time
        self.ul.USER_LIST[userID].setjobenergy(jobID,TRANSPOTTIME) #Task transmission energy consumption calculation
        self.commEnergy += self.ul.USER_LIST[userID].JOB_LIST[jobID].jobCEnergy #The user spends the total task to transfer energy
        self.TRANS_POOL.append((userID,jobID)) #Task joins the transfer pool
    
    def runremote(self,env, WAITING_LEN):#Remote execution
        while True:
            yield env.timeout(self.TIMER)

            if self.SYS_CPU > 0.8: #CPU overload
                yield env.timeout(self.TIMER*2)
                self.SCORE = -abs(self.SCORE)
                continue
            else:
                yield WAITING_LEN.get(1) #Get a task from the waiting list
                job = self.WAITING_LIST.pop()
                userID = job['userID']
                jobID = job['jobID']
                
                self.JOB_POOL.append((userID,jobID)) #Put tasks into the execution queue pool
                self.SYS_CPU += (self.ul.USER_LIST[userID].JOB_LIST[jobID].jobCPU/self.RHO) #Real resource usage
                
                #######################################################################################
                self.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'RR' #Remote execution
                self.ul.USER_LIST[userID].JOB_LIST[jobID].jobBegin = env.now
                RUNNINGTIME = float(self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun)/self.RHO#Really required execution time
                self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRT = RUNNINGTIME
                self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft = RUNNINGTIME
    
    ######Refresh system-transmission part######
    def refreshtrans(self,env,WAITING_LEN):
        while True:
           
            yield env.timeout(self.TIMER)
            transpool = []
            for Jt in self.TRANS_POOL:
                userID = Jt[0]
                jobID = Jt[1]
                onejob = self.ul.USER_LIST[userID].JOB_LIST[jobID]
                
                if onejob.jobTransLeft > self.TIMER:
                    transpool.append((userID,jobID))
                    self.ul.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft = self.ul.USER_LIST[userID].JOB_LIST[jobID].jobTransLeft-self.TIMER
                else:
                    self.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'RW' 
                    self.CHANNEL_USED -= self.ul.USER_LIST[userID].JOB_LIST[jobID].jobChannel
                    self.WAITING_LIST.append({'userID':userID,'jobID':jobID})
                    self.ul.USER_LIST[userID].jobappend()
                    yield WAITING_LEN.put(1)
            self.TRANS_POOL = transpool
            
    ######Refresh system-execution part######
    def refreshsys(self,env, name='',value='',flag = 1):
        if flag ==1:
            f = open('.\\data\\ACTION_'+str(name)+'_'+str(value)+'.data','w')
            oneline = 'sysTime \t'+'Action \t'+'ChannelUsed \t'+'TransJob \t'+'CPU \t'+'RunningJob \t'+'ActionQos \n'
            f.write(oneline)
            f.close()
        while True:
            yield env.timeout(self.TIMER)
            self.SYS_TIME = env.now
             
            jobpool = []
            for Jr in self.JOB_POOL:
                userID = Jr[0]
                jobID = Jr[1]
                onejob = self.ul.USER_LIST[userID].JOB_LIST[jobID]
                
                if onejob.jobRunLeft > self.TIMER:
                    jobpool.append((userID,jobID))
                    self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft = self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRunLeft-self.TIMER
                else:
                    if flag ==1 :
                        f = open('.\\data\\ACTION_'+str(name)+'_'+str(value)+'.data','a')
                        oneline = str(self.SYS_TIME)+'\t' +str(self.ACTION)+'\t' +str(self.CHANNEL_USED)+ '\t' + str(len(self.TRANS_POOL)) + '\t' +str(self.SYS_CPU)+ '\t' + str(len(self.JOB_POOL))
                        oneline += '\t' +str(self.SCORE) + '\n'
                        f.write(oneline)
                    self.SYS_CPU -= (self.ul.USER_LIST[userID].jobCPU/self.RHO) 
                    self.ul.USER_LIST[userID].jobrefresh(env,self.ul.USER_LIST[userID].JOB_LIST[jobID])
                    self.offloadJob.append(self.ul.USER_LIST[userID].JOB_LIST[jobID]) 
                    ##########################log##############################################################
                    self.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge = env.now - self.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    self.Age += self.ul.USER_LIST[userID].JOB_LIST[jobID].jobAge
                    self.Run += self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun 
                    self.commTime += self.ul.USER_LIST[userID].JOB_LIST[jobID].jobTT
                    self.Throughout += 1 
                    ###################################REWARD######################################                   
                    score = self.ul.USER_LIST[userID].JOB_LIST[jobID].jobRun/self.ul.USER_LIST[userID].JOB_LIST[jobID].jobCEnergy

                    self.SCORE = score
                    self.ul.USER_LIST[userID].JOB_LIST[jobID].jobState = 'CP'  
                    self.REWARD += self.SCORE
    
                    self.PRIORITY_LIST[userID] = self.SCORE
                    self.ul.USER_LIST[userID].userPriority[self.mecID] = self.SCORE
                    
                    
                    #################################################################################
            self.JOB_POOL = jobpool
        f.close()
    ######################
    
    #offloading                
    def offloadDQ(self, env,WAITING_LEN,ql):#deep Q learning
        counter = 0
        while True:
            counter += 1
            yield env.timeout(self.TIMER)
            
            if (self.CHANNEL - self.CHANNEL_USED <= 1) or (self.SYS_CPU > 0.9): 
                self.SCORE = -abs(self.SCORE)
                yield env.timeout(self.TIMER*self.Delta)
                continue
            else:
                observation = self.getstate()
                self.ACTION  = ql.RL.choose_action(observation) 
                if (counter < UN*5) or (counter % 10 == 0):
                    pkey = random.sample([i for i in range(UN)],k = self.ACTION)
                else:
                    plist = sorted(self.PRIORITY_LIST.items(),key = lambda i : i[1],reverse= 1)
                    pkey = [plist[i][0] for i in range(len(plist))][:self.ACTION]
                for i in range(len(pkey)):
                    userID = pkey[i]
                    self.offloadOne(env,userID)
            
            