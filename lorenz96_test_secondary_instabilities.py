#!/home/user/anaconda3/bin/python
import numpy as np
import os
import l96
from scipy import triu
import scipy.linalg as linalg
from itertools import product
from sklearn import preprocessing
import warnings
import matplotlib.pyplot as plt
warnings.simplefilter("error")
warnings.simplefilter("ignore", DeprecationWarning)

# these are our constants
paraL96_2lay = {'F1' : 10,
           'F2' : 0,
           'b'  : 10,
           'c'  : 10,
           'h'  : 1,
           'dimX': 36,
           'dimY' : 10,
           'RescaledY' : False,
           'expname' : 'secondaryinstabilities_2layer',
           'time' : np.arange(0,2000,0.1),
           'spinup' : 100,
           '2lay' : True
           }

paraL96_1lay = {'F1' : 10,
           'F2' : 0,
           'b'  : 10,
           'c'  : 10,
           'h'  : 1,
           'dimX': 44,
           'dimY' : 10,
           'RescaledY' : False,
           'expname' : 'secondaryinstabilities_1layer',
           'time' : np.arange(0,1000,0.1),
           'spinup' : 100,
           '2lay' : False
           }


testzeroclv=True

hs=[1.0] #, 0.5] #   ,  0.0625,  0.125 ,  0.25  ,  0.5   ,  1.    ]
experiments = [paraL96_1lay]#,paraL96_2lay]#,paraL96_1lay]    
integrator = 'classic'

# first test clv
epsilons=10.0**np.arange(-8,3,1)
intsteps=np.arange(1,21,1)


timeintervall = range(2000,8000,intsteps.max())
for paraL96,h in product(experiments ,hs):
    if not paraL96['2lay'] and not h == 1.0: print("1 lay only with h = 1.");break
    savename=paraL96['expname']+"_h_"+str(h)
    spinup = paraL96['spinup']        
    paraL96=np.load(savename+"/paraL96.npy")
    paraL96=paraL96[()]
    # M number exponents
    if paraL96['2lay']:
        M = paraL96['dimX'] + paraL96['dimX']*paraL96['dimY'] # -1 full spectrum
        dimN = paraL96['dimX'] + paraL96['dimX']*paraL96['dimY'] # -1 full spectrum
    else:
        M = paraL96['dimX'] 
        dimN = paraL96['dimX'] 
    
        steplengthforsecondorder = np.load(savename+'/steplengthforsecondorder.npy')
    CLVs=np.arange(1,dimN,1)
    dtau=np.mean(np.diff(paraL96['time']))
    t = paraL96['time'][timeintervall]
    correlation=[]
    correlationv2=[]
    realgrowth=[]
    for clv in CLVs:
            correlation.append(np.memmap(savename+'/correlation_clv'+str(clv)+'.dat',mode='w+',shape=(len(intsteps),len(epsilons),len(paraL96['time'])),dtype='float64'))
            correlationv2.append(np.memmap(savename+'/correlationv2_clv'+str(clv)+'.dat',mode='w+',shape=(len(intsteps),len(epsilons),len(paraL96['time'])),dtype='float64'))
            realgrowth.append(np.memmap(savename+'/realgrowth_clv'+str(clv)+'.dat',mode='w+',shape=(len(intsteps),len(epsilons),len(paraL96['time'])),dtype='float64'))

    CLV = np.memmap(savename+'/CLV.dat',mode='r',shape=(len(paraL96['time']),dimN,M),dtype='float64')
    lyaploc_clv = np.memmap(savename+'/lyaploc_clv',mode='r',shape=(len(paraL96['time']),M),dtype='float64')
    trajectory = np.memmap(savename+'/trajectory.dat',mode='r',shape=(len(paraL96['time']),dimN),dtype='float64')
    
    
    precision='float32'
    
    full_solution = np.memmap(savename+'/full_solution.dat',mode='r',shape=(len(steplengthforsecondorder),len(paraL96['time']),dimN,M),dtype=precision)
    
    
    if paraL96['2lay']: L96,L96Jac,L96JacV,L96JacFull,dimN = l96.setupL96_2layer(paraL96)
    else: L96,L96Jac,L96JacV,L96JacFull,dimN = l96.setupL96(paraL96)
    
    field = l96.GinelliForward(dimN,M,tendfunc = L96, jacfunc = L96Jac, jacVfunc = L96JacV,jacfull=L96JacFull, integrator=integrator)
    for tn in timeintervall:
        print(tn)
        
        for en,epsilon in enumerate(epsilons):
            for n, clv in enumerate(CLVs):
                clv=clv-1
                field.x['back']=trajectory[tn,:]+epsilon*CLV[tn,:,clv]
                for step, stepsize in enumerate(intsteps):
                    field.integrate_back(dtau)
                    correlation[n][step,en,tn] = np.sum(np.multiply(preprocessing.normalize(field.x['back'] - trajectory[tn+stepsize,:]),CLV[tn+stepsize,:,clv]))
                    correlationv2[n][step,en,tn] = np.sum(np.multiply(preprocessing.normalize(field.x['back'] - trajectory[tn+stepsize,:]-epsilon*CLV[tn+stepsize,:,clv]),preprocessing.normalize(full_solution[stepsize,tn,:,clv])))
                    realgrowth[n][step,en,tn] = np.log(np.sqrt(np.sum((field.x['back'] - trajectory[tn+stepsize,:])**2))/epsilon)/(dtau*(stepsize))
                    
                
        if tn % 100 == 0:
            for n, clv in enumerate(CLVs):
                np.memmap.flush(realgrowth[n])
                np.memmap.flush(correlation[n])
            
    np.save(savename+"/timeintervall", timeintervall)
    np.save(savename+"/epsilons",epsilons)        
    np.save(savename+"/intsteps",intsteps)        
    print("Saveing results in folder "+savename+".")
