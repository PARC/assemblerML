#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 19:25:54 2019
@author: Kent Evans

The idea here is to have a neural net control the gains of a PID controller.
Essentially, the idea here is to introduce some feed forward control by 
having the net learn on current state, desired state for the next N time steps
and various gains.

The loss function will, at least initially, be defined as the sum of the MSE between the
setpoint and trajectory at every point in time.

I don't think this will work for any arbitrary path.  We will have to train for 
every unique path?  Don't see a clear way forward for that.

Network architecture:
   
INPUT                   HIDDEN              OUTPUT
   x|t                                      Kp|t+1
   xdot|tC                                  Ki|T+1
   r|t+1                                    Kd|t+1
   rdot|t+1          FC 64 - FC 3
   ...
   r|t+L+1
   rdot|t+L+1  (r/rdot)
   Kp|t
   Ki|t   
   Kd|t 

Try both with and without gains in the input to the next layer.

state variables:
  speed = x1
  acceleration = x2


@TODO
    -Weight normalization step
    -noise to simulation output
    -Inspect an existing RNN solution for ideas/pitfalls

IDEAS
    - Piece together trajectories to train on randomly (random selection of trajectory segments)


"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import numpy as np
#Making small change to test VCS with gitlab and pycharm

class motor:
    def __init__(self , tC ):
        self.L = .5
        self.R = 1
        self.J = .01
        self.b = .1
        self.Kb = .01
        self.Km = .01
        self.C = np.array([1.0,0])
        self.A = np.array([[0,1.0],[-(self.R*self.b-self.Km*self.Kb)/(self.L*self.J),-(self.L*self.b+self.R*self.J)/(self.L*self.J)]])
        self.B = np.array([[0],[self.Km/(self.L*self.J)]])
        self.D = np.array([0.0])
        self.tC = tC
        self.dTc = tC[1]-tC[0]
        
        self.lastError = 0
        self.currError = 0
        self.totalError = 0
        
        self.state = np.zeros([2,1])
        self.statedot = np.zeros((2,1))
        self.result = np.zeros([2,len(self.tC)])
        self.resultLoc = 0
        
        self.gains = np.array([[125],[50],[5]])
        self.simCount = 0
        
    def getInput(self):
        #Implement PID controller
        return self.gains[0]*self.currError + self.gains[1]*self.totalError + self.gains[2]*(self.currError-self.lastError)/self.dTc

    def simulateStep( self , ref , simsteps = 1 ):
        if self.resultLoc == 0 or self.resultLoc >= len(self.tC):
            self.resultLoc = 0
            self.state = np.zeros([2,1])
        for i in range(simsteps):
            self.updateErrors(ref)
            self.statedot = np.matmul(self.A,self.state) + self.B*self.getInput()
            self.state += self.statedot*self.dTc
            self.result[:,self.resultLoc,None] = self.state
            self.resultLoc += 1
        return self.state
    
    def simulate(self,ref):
        #Look for exisiting results, if doesn't exist create a new bin for them.  Structure is position in first row, velocity in second
        self.state = np.zeros([2,1])
        if (self.simCount == 0):
            self.simulationResults = np.zeros((2,len(self.tC)))
        else:
            self.simulationResults = np.stack((self.simulationResults,np.zeros((2,len(self.tC)))))
                
        for i in range(len(self.tC)):
            self.updateErrors(ref[i])
            self.statedot = np.matmul(self.A,self.state) + self.B*self.getInput()
            self.state += self.statedot*self.dTc
            if self.simCount == 0:
                self.simulationResults[:,i,None] = self.state
            else:
                self.simulationResults[self.simCount,:,i,None] = self.state
            
        self.simCount += 1
        return

    def updateErrors(self,ref):
        self.lastError = self.currError
        self.currError = ref - self.state[0]
        self.totalError += self.currError*self.dTc

class PIDnet(nn.Module):
    def __init__(self, n_state = 2, n_hid = 64, n_steps = 6, incl_gains = False):
        super(PIDnet,self).__init__()
        self.incl_gains = incl_gains
        if incl_gains:
            self.n_gains = 3
        else:
            self.n_gains = 0
        self.hidden_size = n_hid
        self.input_size = n_state + n_state*n_steps + self.n_gains
        """
        Network Layer Definitions
            Start with one hidden layer.
            weight normalizations!
        
        """
        self.i2h1 = nn.LeakyReLU(nn.Linear(self.input_size,self.hidden_size))
        self.h12o = nn.LeakyReLU(nn.Linear(self.hidden_size,3))

    def forward(self , inp , hid, gains):
        if self.incl_gains:
            hidden = self.i2h1(torch.cat(torch.cat(inp,hid,1),gains,1))
        else:
            hidden = self.i2h1(torch.cat(inp,hid,1))
        output = self.h12o(hidden)
        return output , hidden

    def newHidden(self):
        return torch.zeros(1,self.hidden_size)

    """
        At start I have:
            - State
            - 

    """

pid = PIDnet()


t = np.arange(0,10,.01)
mot = motor(t)
r1 = np.sin(t)
mot.simulate(r1)
r2 = np.ones(len(t))
r2[100:200]=2
r2[300:400]=8
r2[500:600]=0
r2[700:800]=5
r2[900:1000]=1
mot.simulate(r2)
plt.figure(0)
#Sine Wave Plot
plt.subplot(1,2,1)
plt.plot(t,r1,t,mot.simulationResults[0,0,:])
plt.gca().legend(('setpt','motor'))
#Step Plots
plt.subplot(1,2,2)
plt.plot(t,r2,t,mot.simulationResults[1,0,:])
plt.gca().legend(('setpt','motor'))
plt.show()
plt.savefig("PIDnet.jpg")