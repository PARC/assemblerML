# Please change the root variable as required.
# train and test directories of the dataset need to be present in the root directory
# weights need to be present in a weights folder in the root directory

from Problems.DCMotor import *
from Models.Dense import* 
from Models.StateSpace import* 
from Models.RNN import* 
#from Models.LSTM import* 
from Operators.Ensemble import* 
from Operators.Cyclic import* 
from Operators.Boosting import* 
from Evaluation.Evaluate import* 
import pandas as pd

Name="1Input1OutputSS"

m = Motor()

time_step=1
output_time_step=1

input_size=m.input_size
output_size=m.output_size


model = SSModel(time_step=time_step,output_time_step=output_time_step,input_size=input_size,output_size=output_size)



timemotor=np.load("timemotor.npy")

X=np.load("RealData/X10Hz.npy")
y=np.load("RealData/y10Hz.npy")

X100=np.load("RealData/X100Hz.npy")
y100=np.load("RealData/y100Hz.npy")

X1=np.load("RealData/X1Hz.npy")
y1=np.load("RealData/y1Hz.npy")


model.fit(X,[y],epochs=100,batch_size=32)

print(model.get_weights())
print(model.get_weights)

out=model.predict(X)

result=np.concatenate((out[:,[-1],:],y[:,[-1],:]+X[:,[-1],0:output_size],X[:,[-1],:]),axis=2)

result=result.reshape(len(X),output_size*3+1)

timemotor=timemotor.reshape(len(timemotor),1)
timemotor=timemotor[:len(timemotor)-1]

result=np.concatenate((result,timemotor),axis=1)
evaluate(result,output_size=output_size,Training_Time=0,name="RealData/Images/10Hz"+Name)

#ExtrapolationDataset100HZ

out=model.predict(X100)

result=np.concatenate((out[:,[-1],:],y100[:,[-1],:]+X100[:,[-1],0:output_size],X100[:,[-1],:]),axis=2)

result=result.reshape(len(X100),output_size*3+1)

#timemotor=timemotor.reshape(len(timemotor),1)
#timemotor=timemotor[:len(timemotor)-1]

result=np.concatenate((result,timemotor),axis=1)
evaluate(result,output_size=output_size,Training_Time=0,name="RealData/Images/Extrapolation100Hz"+Name)

#ExtrapolationDataset1HZ

out=model.predict(X1)

result=np.concatenate((out[:,[-1],:],y1[:,[-1],:]+X1[:,[-1],0:output_size],X1[:,[-1],:]),axis=2)

result=result.reshape(len(X1),output_size*3+1)

#timemotor=timemotor.reshape(len(timemotor),1)
#timemotor=timemotor[:len(timemotor)-1]

result=np.concatenate((result,timemotor),axis=1)
evaluate(result,output_size=output_size,Training_Time=0,name="RealData/Images/Extrapolation1Hz"+Name)
