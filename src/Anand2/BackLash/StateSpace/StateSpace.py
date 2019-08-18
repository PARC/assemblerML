# Please change the root variable as required.
# train and test directories of the dataset need to be present in the root directory
# weights need to be present in a weights folder in the root directory

from Evaluate import *

from sklearn.utils import class_weight
from keras import applications
from keras.models import Sequential
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD
import cv2, numpy as np
from sklearn.model_selection import StratifiedKFold,KFold,train_test_split

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2, pandas as pd
import numpy as np
import h5py
import pickle, math

from pandas.tools.plotting import autocorrelation_plot
#from statsmodels.graphics.gofplots import qqplot

from scipy.stats import probplot as qqplot


import keras
from keras.layers.advanced_activations import LeakyReLU, PReLU,ELU
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Convolution2D, Dense, Input, MaxPooling2D, Dropout, Flatten, ZeroPadding2D, Activation,LSTM,Bidirectional,Convolution1D,MaxPooling1D,Conv1D,SimpleRNN,Lambda
from keras.layers.pooling import AveragePooling2D,GlobalAveragePooling1D
from keras.models import Model, Sequential
from keras.utils.vis_utils import plot_model
from keras.optimizers import SGD, Adam
from keras.regularizers import l2
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, ReduceLROnPlateau,EarlyStopping
from sklearn.metrics import roc_auc_score, accuracy_score
import keras.backend as K
from keras.preprocessing.image import ImageDataGenerator
from keras import regularizers
from keras.metrics import categorical_accuracy
from sklearn.preprocessing import LabelEncoder
from keras.utils import np_utils
from sklearn.metrics import mean_squared_error as mse, r2_score as r2

np.random.seed(1)


def NormCrossCorr(a,b,mode='same'):
	a = (a - np.mean(a)) / (np.std(a) * len(a))
	b = (b - np.mean(b)) / (np.std(b))
	c = np.correlate(a, b, mode)
	return c




class Motor:
    def __init__(self):
        self.L = .5
        self.R = 1
        self.J = 0.01
        self.b = .1
        self.Kb = .01
        self.Km = .01
        self.C = np.array([1.0, 0])
        self.A = np.array([[0, 1.0], [-(self.R * self.b - self.Km * self.Kb) / (self.L * self.J),
                                      -(self.L * self.b + self.R * self.J) / (self.L * self.J)]])
        self.B = np.array([[0], [self.Km / (self.L * self.J)]])
        self.D = np.array([0.0])
        self.dT = 0.0

        self.state = np.zeros([1,2], dtype=float)
        self.TRstate = np.zeros([1,2], dtype=float)
        self.stateDot = np.zeros([1,2], dtype=float)

    def setTimeStep(self, dT):
        self.dT = dT
        return

    def step(self, u):
        self.stateDot = np.matmul(self.A, self.state.transpose()) + self.B * u
        self.state += self.stateDot.transpose() * self.dT

	if self.TRstate[:,0]>=0:
		if (self.TRstate[:,0]-self.state[:,0]>0.005):	
			print "Inside the Backlash Update"
			print self.TRstate,self.state
			self.TRstate=np.array(list(self.state))
		else:
			self.TRstate=self.TRstate
	elif self.TRstate[:,0]<0:
		if (self.state[:,0]-self.TRstate[:,0]>0.005):	
			print "Inside the Backlash Update"
			print self.TRstate,self.state
			self.TRstate=np.array(list(self.state))
		else:
			self.TRstate=self.TRstate
	#else:
	#	print "Inside zero"	
	#	self.TRstate=np.array(list(self.state))

		
        return self.TRstate
    def update(self):
        self.C = np.array([1.0, 0])
        self.A = np.array([[0, 1.0], [-(self.R * self.b - self.Km * self.Kb) / (self.L * self.J),
                                      -(self.L * self.b + self.R * self.J) / (self.L * self.J)]])
        self.B = np.array([[0], [self.Km / (self.L * self.J)]])
        self.D = np.array([0.0])


def getControlInput():
    out = np.random.rand() * 20 - 10
    #out = np.random.rand() * 20
    return out


def densemodel():
        input = Input(batch_shape=(None,3))
        output = Dense(2,activation="linear",use_bias=False)(input)
        model = Model(inputs=input, outputs=output)
        model.compile(loss="mse", optimizer='adam', metrics=['accuracy'])
        return model


def rnnmodel():
        input = Input(batch_shape=(None,1,3))
        x=SimpleRNN(10,activation="relu",return_sequences=True)(input)
        x=SimpleRNN(10,activation="relu")(x)
        x = Dense(10)(x)
        output = Dense(2)(x)
        model = Model(inputs=input, outputs=output)
	adam=keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
        model.compile(loss="mse", optimizer=adam, metrics=['accuracy','mse'])
        return model


m = Motor()
dT = .001
m.setTimeStep(dT)
model = densemodel()
result = np.zeros([8,1])
printDuring=False

X=[]
y=[]
controlaction=np.sin((np.arange(0,50,0.0001)))
for i in np.arange(0, 50000):
    # StepWise control input function
    if (i%100==0):
    	controlInput=10*controlaction[i]
		
    stateTensor =(m.TRstate)
    stateTensor = np.concatenate((stateTensor,(np.ones([1,1], dtype=float) * controlInput)), 1)
    outBar=m.step(controlInput)

    #print "Current State, Next State, True Difference", stateTensor[:,0:2],outBar,outBar-stateTensor[0,0:2]
    if i<10000:
        out=np.zeros((1,2))
        X.append(stateTensor)
        y.append(outBar-stateTensor[:,0:2])
    elif i==10000:
        out=np.zeros((1,2))
        model.fit(np.asarray(X).reshape(10000,3),(np.asarray(y)).reshape(10000,2),epochs=50,batch_size=32)
    elif i>10000:
    	out=model.predict(stateTensor)
    else:
	continue
    tmpResult = np.empty([8,1])
    tmpResult[0] = dT*(i+1)
    tmpResult[1] = out[0][0]
    tmpResult[2] = outBar[0][0]
    tmpResult[3] = out[0][1]
    tmpResult[4] = outBar[0][1]
    tmpResult[5] = controlInput
    tmpResult[6] = stateTensor[:,0]
    tmpResult[7] = stateTensor[:,1]
    result = np.concatenate((result,tmpResult),1)


evaluate(result,"StateSpace")
weights=model.get_weights()
print weights
print m.A, m.B