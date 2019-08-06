# Please change the root variable as required.
# train and test directories of the dataset need to be present in the root directory
# weights need to be present in a weights folder in the root directory

from Problems.NNDelay import *
from numpy import sin,cos,pi
from Models.ControlDense import* 
from Models.Dense import* 
from Models.StateSpace import* 
from Models.RNN import* 
from Operators.Ensemble import* 
from Operators.Boosting import* 
from Operators.NNCyclicControl import* 
from Evaluation.EvaluateControl import* 
import pandas as pd

Name="NNDelayController"
import time

m = NNDelay()

dT=0.1
m.setTimeStep(dT)
time_step=10
output_time_step=1

input_size=m.input_size
output_size=m.output_size

#model1 = ControlDenseModel(time_step=time_step,output_time_step=output_time_step,input_size=4,output_size=1)
model1 = DenseModel(time_step=time_step,output_time_step=output_time_step,input_size=input_size+1,output_size=1,output_function="tanh",depth=3,scaling=10)
model2 = RNNModel(time_step=time_step,output_time_step=output_time_step,input_size=input_size,output_size=output_size,output_function="linear",depth=3)
#model2 = SSModel(time_step=time_step,output_time_step=output_time_step,input_size=input_size,output_size=output_size)
model3 = DenseModel(time_step=output_time_step,output_time_step=time_step,input_size=output_size,output_size=input_size,output_function="linear",depth=3)

X=[]
y=[]

controlaction=np.sin(np.arange(0,25000)*(np.pi/180))*10


moving_input=np.zeros((time_step,input_size))
moving_output=np.zeros((output_time_step,output_size))
controlInput=np.zeros((1,1))
for i in np.arange(0,25000):
    # control input function
	if i>0 and i%5000==0:
		#moving_input=np.zeros((time_step,input_size))
		#m.reset()
		print ("Loop Number-",i)
	stateTensor=m.state
	controlInput[:]=np.array(controlaction[i])
	#controlInput[:]=m.getControlInput()
	stateTensor=np.append(stateTensor,controlInput,-1)
	outBar=m.step(controlInput[0][0])

	if time_step>1: #To shift Inputs to the left
		moving_input[0:time_step-1,:]=moving_input[1:time_step,:]

	moving_input[time_step-1,:]=stateTensor
	moving_input2=np.asarray(list(moving_input))

	if output_time_step>1:
		moving_output[0:output_time_step-1,:]=moving_output[1:output_time_step,:]

	moving_output[output_time_step-1,:]=outBar-stateTensor[:,0:output_size]
	#moving_output[output_time_step-1,:]=outBar
	moving_output2=np.asarray(list(moving_output))

	X.append(moving_input2)
	y.append(moving_output2)


X=np.asarray(X)
y=np.asarray(y)
model2.fit(X,y,epochs=200,batch_size=512)


plt.figure(1,figsize=(20,10))
plt.subplot(2, 1,1)
plt.plot(X[:,-1,0],c="k",linewidth="4",label="CurrentState")
plt.ylabel("State:0")
plt.legend(loc="upper right")

plt.subplot(2, 1,2)
plt.plot(X[:,-1,-1],c="r",label="ControlInput")
plt.ylabel("Control Input")
plt.xlabel("Time")
plt.legend(loc="upper right")
plt.show()
plt.savefig("TImeDelayResopnse.svg")
plt.clf()


model2.trainable=False

print (model2.summary())
print (model2.get_weights())


model,modeltrue=CyclicControlModel(model1,model2,model3,input_size=1,time_step=time_step)
print (model.summary())

m.reset()
stateTensor=m.state
stateTensor=stateTensor.reshape(1,1,1)
ref=np.array([10.0])
ref=ref.reshape(1,1,1)
ref=np.repeat(ref,time_step,axis=1)
controlInput=np.zeros((1,time_step,1))
stateNew=np.array(stateTensor)
PrevPosition=np.array(stateTensor)

X1=[]
X2=[]
X3=[]

moving_input=np.zeros((1,time_step,input_size-1))
moving_input[:,-1,:]=np.array(stateTensor)

for i in np.arange(0,800):
	#print ("Reference State,True State, Previous State, Predicted State,Control Action,Loop Count",ref,stateTensor,PrevPosition,stateNew,controlInput,i)
	print ("Reference State,True State,Previous State,Predicted State,Control Action,Loop Count",ref[:,0,:],stateTensor[:,:,:],PrevPosition[:,-1,:],stateNew[:,-1,:],controlInput[:,-1,:],i)
	#time.sleep(0.1)
	if i<=200:
		ref[:,-1,:]=3
	elif i>200 and i<=400:
		ref[:,-1,:]=30
	elif i>400 and i<=500:
		ref[:,-1,:]=100
	elif i>500 and i<=600:
		ref[:,-1,:]=10
	else:
		ref[:,-1,:]-=10*dT
		

	#controlInput,stateTensor,PrevPosition=modeltrue.predict([stateTensor,ref-stateTensor,controlInput])
	controlInput[:,-1,:],stateTensor,PrevPosition=modeltrue.predict([moving_input,ref,controlInput])
	#controlInput,stateTensor=modeltrue.predict([stateTensor,ref,controlInput])
	X1.append(np.array(stateTensor))
	X2.append(np.array(ref[:,-1,:]))
	X3.append(np.array(controlInput[:,-1,:]))
	moving_input[:,-1,:]=np.array(stateTensor)



	model.fit([moving_input,ref,controlInput],[ref[:,[-1],:],np.concatenate([moving_input,controlInput],axis=2)],epochs=100,verbose=0)
	stateNew=np.array(stateTensor)	
	stateTensor=m.step(controlInput[:,-1,:])
	stateTensor=stateTensor.reshape(1,1,1)
	moving_input[:,-1,:]=np.array(stateTensor)

	if time_step>1: #To shift Inputs to the left
		moving_input[:,0:time_step-1,:]=np.array(moving_input[:,1:time_step,:])
		controlInput[:,0:time_step-1,:]=np.array(controlInput[:,1:time_step,:])
		ref[:,0:time_step-1,:]=np.array(ref[:,1:time_step,:])

		

X1=np.reshape(np.asarray(X1),(len(X1),1))
X2=np.reshape(np.asarray(X2),(len(X2),1))
X3=np.reshape(np.asarray(X3),(len(X3),1))

X=np.concatenate([X1,X2,X3],axis=-1)

evaluate(X,name="Images/NN-Delay-CyclicControl-M1RNN-M2RNN-M3RNN-LookBack10",output_size=1)
