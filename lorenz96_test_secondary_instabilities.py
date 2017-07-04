#!/home/user/anaconda3/bin/python
import numpy as np
import os
import l96
from scipy import triu
import scipy.linalg as linalg
from itertools import product
#from sklearn import preprocessing
import warnings
import matplotlib.pyplot as plt
warnings.simplefilter("error")
warnings.simplefilter("ignore", DeprecationWarning)

norm = lambda x : np.sqrt(np.sum(x**2.0))
normalize = lambda x : x/norm(x)

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
epsilons=10.0**np.arange(-9,1,1)
intsteps=np.arange(1,100,1)

precision='float64'

CLVs=[1, 5 , 13, 18 , 40]
timeintervall = range(2000  ,8011,100)
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
    
    np.save(savename+"/CLVs",CLVs)
    dtau=np.mean(np.diff(paraL96['time']))
    t = paraL96['time'][timeintervall]
    correlation=[]
    correlationv2=[]
    correlationv3=[]
    realgrowth=[]
    normerror = []
    for clv in CLVs:
        correlation.append(np.memmap(savename+'/correlation_only_1_clv'+str(clv)+'.dat',mode='w+',shape=(len(paraL96['time']),len(intsteps),len(epsilons)),dtype='float64'))
        correlationv2.append(np.memmap(savename+'/correlation_1and2_clv'+str(clv)+'.dat',mode='w+',shape=(len(paraL96['time']),len(intsteps),len(epsilons)),dtype='float64'))
        correlationv3.append(np.memmap(savename+'/correlation_only_2_clv'+str(clv)+'.dat',mode='w+',shape=(len(paraL96['time']),len(intsteps),len(epsilons)),dtype='float64'))
        normerror.append(np.memmap(savename+'/normerror_clv'+str(clv)+'.dat',mode='w+',shape=(len(paraL96['time']),len(intsteps),len(epsilons)),dtype='float64'))
        realgrowth.append(np.memmap(savename+'/realgrowth_clv'+str(clv)+'.dat',mode='w+',shape=(len(paraL96['time']),len(intsteps),len(epsilons)),dtype='float64'))
 
    measured=np.memmap(savename+'/measuredgrowth.dat',mode='w+',shape=(len(CLVs),len(intsteps),len(paraL96['time'])),dtype='float64')
    CLV = np.memmap(savename+'/CLV.dat',mode='r',shape=(len(paraL96['time']),dimN,M),dtype='float64')
    lyaploc_clv = np.memmap(savename+'/lyaploc_clv',mode='r',shape=(len(paraL96['time']),M),dtype='float64')
    trajectory = np.memmap(savename+'/trajectory.dat',mode='r',shape=(len(paraL96['time']),dimN),dtype='float64')
    
    
    
    full_solution = np.memmap(savename+'/full_solution.dat',mode='r',shape=(len(paraL96['time']),len(steplengthforsecondorder),dimN,M),dtype=precision)
    lyaploc_clv = np.memmap(savename+'/lyaploc_clv',mode='r',shape=(len(paraL96['time']),M),dtype='float64')
    
    if paraL96['2lay']: L96,L96Jac,L96JacV,L96JacFull,dimN = l96.setupL96_2layer(paraL96)
    else: L96,L96Jac,L96JacV,L96JacFull,dimN = l96.setupL96(paraL96)
    
    field = l96.GinelliForward(dimN,M,tendfunc = L96, jacfunc = L96Jac, jacVfunc = L96JacV,jacfull=L96JacFull, integrator=integrator)
    for i,tn in enumerate(timeintervall):
        print(tn)
        
        for en,epsilon in enumerate(epsilons):
            print(' eps: '+str(epsilon))
            for nc, clv in enumerate(CLVs):
                field.x['back']=trajectory[tn,:]+epsilon*CLV[tn,:,clv-1]
                for step, stepsize in enumerate(intsteps):
                    field.integrate_back(dtau)
                    correlation[nc][tn,step,en] = np.sum(np.multiply(normalize(field.x['back'] - trajectory[tn+stepsize,:]),CLV[tn+stepsize,:,clv-1]))
                    correlationv2[nc][tn,step,en] = np.sum(np.multiply(normalize(field.x['back'] - 
                    trajectory[tn+stepsize,:]),normalize(full_solution[tn,stepsize,:,clv-1]*epsilon**2.0+
                    epsilon*CLV[tn+stepsize,:,clv-1]*np.exp(dtau*np.memmap.sum(lyaploc_clv[tn:tn+stepsize,clv-1])))))
                    correlationv3[nc][tn,step,en] = np.sum(np.multiply(normalize(field.x['back'] - 
                    trajectory[tn+stepsize,:]),normalize(full_solution[tn,stepsize,:,clv-1]*epsilon**2.0)))
                    realgrowth[nc][tn,step,en] = np.log(np.sqrt(np.sum((field.x['back'] - trajectory[tn+stepsize,:])**2.0))/epsilon)/(dtau*(stepsize))
                    #measured[nc,step,tn]=np.mean(lyaploc_clv[tn:tn+stepsize,clv-1])
                    normerror[nc][tn,step,en] = norm(field.x['back'] - trajectory[tn+stepsize,:] - full_solution[tn,stepsize,:,clv-1]*epsilon**2.0-
                    epsilon*CLV[tn+stepsize,:,clv-1]*np.exp(dtau*np.memmap.sum(lyaploc_clv[tn:tn+stepsize,clv-1])))/norm(field.x['back'] - 
                    trajectory[tn+stepsize,:])
                    #print(correlation[nc][tn,step,en])
                
        if i % 10 == 0:
            for nc, clv in enumerate(CLVs):
                np.memmap.flush(realgrowth[nc])
                np.memmap.flush(correlation[nc])
                np.memmap.flush(correlationv2[nc])
                np.memmap.flush(correlationv3[nc])
                np.memmap.flush(normerror[nc])
            print("flushed")

        for nc, clv in enumerate(CLVs):    
            np.memmap.flush(realgrowth[nc])
            np.memmap.flush(correlation[nc])
            np.memmap.flush(correlationv2[nc])
            np.memmap.flush(correlationv3[nc])
            np.memmap.flush(normerror[nc])

    np.save(savename+"/timeintervall", timeintervall)
    np.save(savename+"/epsilons",epsilons)        
    np.save(savename+"/intsteps",intsteps)        
    print("Saveing results in folder "+savename+".")
