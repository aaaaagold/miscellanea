
import os
import sys
import multiprocessing

import math
import random
from decimal import Decimal, Context, getcontext, localcontext

import time
from pprint import pprint


getcontext().prec = 77
printPrec=12


expansionRate=Decimal(1.06**(1.0/250))
changePercentConf={
"mean":0,
"sigma2":0.03**2, # n*p*(1-p)
}
initCash=10**16
cashRate=Decimal(1.0/32)
initPrices=[Decimal(10**8),]*32
sim1Round=int(sys.argv[1]) if len(sys.argv)>1 else 1250
simsRound=int(sys.argv[2]) if len(sys.argv)>2 else 10**2
paramSel=int(sys.argv[3]) if len(sys.argv)>3 else 0
N=1
balancingThreshold=1.0/8/N # p: 1/8 -> 1/8-1/32 ; th: +- 1/8
rebalancedRatio=Decimal(1.0/8-1.0/32)/N
buyAdjRatio=balancingThreshold
if not paramSel: pass
elif paramSel==2:
	balancingThreshold=0.05/N #
	rebalancedRatio=Decimal(balancingThreshold-.0375)/N
	buyAdjRatio=Decimal(.9875-1)/N
if rebalancedRatio>=balancingThreshold: raise "conf error"


def approximateNoraml(conf,epoch=64,):
	binomialRoundCnt=epoch
	
	val=0
	for i in range(binomialRoundCnt):
		if random.random()<0.5:
			val+=1
	mean=epoch/2.0
	sigma2=epoch/4.0
	return (val-mean)*((conf['sigma2']/sigma2)**0.5)


if 0:
	# test
	obj={}
	for i in range(2**17):
		res=approximateNoraml(changePercentConf)
		if not res in obj: obj[res]=0
		obj[res]+=1
	s=0
	for k in obj: s+=obj[k]
	print(s)
	res=[ [k,obj[k],obj[k]/s] for k in obj ]
	res.sort(key=lambda x:x[0])
	for i in range(1,len(res)): res[i][2]+=res[i-1][2]
	pprint(res)
	print(len(res))
	pass


def getUsableCpus():
	rtv=1
	try:
		import os
		rtv=len(os.sched_getaffinity(0))
	except:
		try:
			import ctypes
			aff_curr=ctypes.c_ulonglong(0)
			aff_sys=ctypes.c_ulonglong(0)
			if ctypes.windll.kernel32.GetProcessAffinityMask(
				ctypes.windll.kernel32.GetCurrentProcess(),
				ctypes.byref(aff_curr),
				ctypes.byref(aff_sys),
			):
				try:
					rtv=aff_curr.bit_count()
				except:
					rtv=bin(int(aff_curr.value)).count('1')
			else:
				# api fail
				rtv=1
		except:
			rtv=1
			pass
	return rtv


def doTest1(globalInfo):
	initCash=globalInfo['initCash']
	prices=globalInfo['initPrices'][:]
	prices0=prices[:]
	shares=[0]*len(prices)
	cash=initCash
	cashAllIn=0
	sharesAllIn=0
	if 1:
		cash1=int(initCash*(1-cashRate)/len(prices))
		for i in range(len(prices)):
			share=int(cash1/prices[i])
			shares[i]+=share
			cash-=share*prices[i]
		pass
		sharesAllIn+=int(int(initCash/len(prices))/prices0[0])
		cashAllIn+=initCash-sharesAllIn*prices0[0]*len(prices)
		pass
	shares0=shares[:]
	cash0=cash
	
	resV0=initCash
	resV=initCash
	weights=[Decimal(x)*prices[i]/initCash for x in shares]
	for _ in range(sim1Round):
		# test threshold
		sumW=cashRate+sum(weights)
		sumP=cash+sum([shares[i]*prices[i] for i in range(len(prices))])
		ratios=[0]*len(prices)
		rs=[0]*len(prices)
		exprs=[0]*len(prices)
		adjSs=[0]*len(prices)
		for i in range(len(prices)):
			if not sumW: break
			if not prices[i]: continue
			c=shares[i]*prices[i]
			ratio=Decimal(c/sumP)
			ratios[i]=ratio
			expRatio=weights[i]/sumW
			if not expRatio:
				adjSs[i]=-shares[i]
				continue
			exprs[i]=expRatio
			r=ratio/expRatio
			rs[i]=r
			expP=sumP*expRatio
			if r==1: continue
			elif 1<r and 1+balancingThreshold<r:
				adjSs[i]+=math.floor((1+rebalancedRatio-r)*expP/prices[i])
			elif not ratio or 1+balancingThreshold<1/r:
				adjSs[i]+=math.ceil((1/(1+rebalancedRatio)-r)*expP/prices[i])
			pass
		
		# change price
		for i in range(len(prices)):
			if not prices[i]: continue
			res=Decimal(approximateNoraml(changePercentConf))
			if res<0:
				prices[i]/=expansionRate-res
			else:
				prices[i]*=expansionRate+res
			prices[i]=int(prices[i])
			if not prices[i]: weights[i]=0
			if prices[i]<0:
				raise "prices[i]<0"
		
		# adjust shares && weights
		adjRatio=1
		totalCost=sum([adjSs[i]*prices[i] for i in range(len(prices))])
		if cash<totalCost:
			adjRatio=Decimal(cash/totalCost)
			print('broke')
			pass
		for i in range(len(prices)):
			if not weights[i]: continue
			if not adjSs[i]: continue
			if adjRatio<1:
				adjSs[i]*=adjRatio
				adjSs[i]=math.floor(adjSs[i])
			cash-=adjSs[i]*prices[i]
			shares[i]+=adjSs[i]
			r=1+buyAdjRatio if adjSs[i]<0 else 1/(1+buyAdjRatio)
			weights[i]*=Decimal(r)
			#print(_,i,weights[i],r)
		if cash<0:
			print()
			print('round',_,'cash<0',cash)
			print('ratios')
			pprint(ratios)
			print('exprs')
			pprint(exprs)
			print('rs')
			pprint(rs)
			print(adjSs)
			print('adjP',[adjSs[i]*prices[i] for i in range(len(prices))])
			print('shares')
			pprint(shares)
			print('prices')
			pprint(prices)
			pprint(weights)
			raise "cash<0"
		resV0=cash0
		for i in range(len(prices)): resV0+=shares0[i]*prices[i]
		resV=cash
		for i in range(len(prices)): resV+=shares[i]*prices[i]
		resAllIn=cashAllIn+sharesAllIn*sum(prices)
		if not globalInfo['outputs']:
			with localcontext() as ctx:
				ctx.prec=printPrec
				print('round',_,
					resV.to_eng_string(),
					resV0.to_eng_string(),
					(resV/resV0).to_eng_string(),
					(resV/initCash).to_eng_string(),
					(resAllIn/initCash).to_eng_string(),
					(resV-resV0).to_eng_string(),
					(resV-initCash).to_eng_string(),
					(resAllIn-initCash).to_eng_string(),
				' '*8,end='\r')
				pass
			pass
		pass
	if not globalInfo['outputs']:
		print()
		print('idx,shares0,shares,prices0,prices')
		for i in range(len(prices)):
			print(i,shares0[i],shares[i],prices0[i],prices[i],sep=',')
		print('cash0')
		pprint(cash0)
		print('cash')
		pprint(cash)
		print('initCash',initCash)
		print('resV0',resV0)
		print('resV',resV)
		print('resAllIn',resAllIn)
		print('resV/resV0',resV/resV0)
		print('resAllIn/resV0',resAllIn/resV0)
		print('resV/initCash',resV/initCash)
		print('resAllIn/initCash',resAllIn/initCash)
	pass
	return [
		float(resV0/initCash),
		float(resV/initCash),
		float(resAllIn/initCash),
	]
	pass


def printResv(resv_src):
	resv=[x for x in resv_src if x]
	resv.sort()
	s=sum(resv)
	L=len(resv)
	m=resv[L>>1] if L&1 else (resv[L>>1]+(resv[(L>>1)-1]))/2.0
	m25=resv[L>>2] if L&3 else (resv[L>>2]+resv[(L>>2)-1])/2.0
	m75=resv[(L*3)>>2] if L&3 else (resv[(L*3)>>2]+resv[((L*3)>>2)-1])/2.0
	m125=resv[L>>3] if L&7 else (resv[L>>3]+resv[(L>>3)-1])/2.0
	m875=resv[(L*7)>>3] if L&7 else (resv[(L*7)>>3]+resv[((L*7)>>3)-1])/2.0
	pprint({
		'mid':m,
		'm25':m25,
		'm75':m75,
		'm125':m125,
		'm875':m875,
		'avg':s/len(resv),
		'min':min(resv),
		'max':max(resv),
		'len':len(resv),
	})

def doTests(globalInfo,idxBeg,idxEnd):
	simsRound=idxEnd-idxBeg
	resv0=[0.0]*simsRound
	resv1=[0.0]*simsRound
	resv2=[0.0]*simsRound
	for i in range(simsRound):
		try:
			res=doTest1(globalInfo)
			resv0[i]=res[0]
			resv1[i]=res[1]
			resv2[i]=res[2]
		except KeyboardInterrupt as e:
			raise e
		except:
			print('broke')
		print(idxBeg,i+1,'/',simsRound)
	if not globalInfo['outputs']:
		return resv0,resv1,resv2
	for i in range(simsRound):
		globalInfo['outputs']['resv0'][idxBeg+i]=resv0[i]
		globalInfo['outputs']['resv1'][idxBeg+i]=resv1[i]
		globalInfo['outputs']['resv2'][idxBeg+i]=resv2[i]
	pass

def doTests_threading(argv):
	parallelCnt=max(1,getUsableCpus()-1) if '--single-cpu' not in argv else 1
	#parallelCnt=1 # debug test
	resv0=multiprocessing.RawArray('d', range(simsRound))
	resv1=multiprocessing.RawArray('d', range(simsRound))
	resv2=multiprocessing.RawArray('d', range(simsRound))
	globalInfo_src={
		'outputs':{
			'resv0':resv0, # 1-cashRate
			'resv1':resv1, # dynamic
			'resv2':resv2, # 100%
		},
		'initCash':initCash,
		'initPrices':initPrices[:],
		'cashRate':Decimal(cashRate),
	}
	if 1<parallelCnt:
		starts=[simsRound*i//parallelCnt for i in range(parallelCnt)]
		starts.append(simsRound)
		threads=[]
		for i in range(parallelCnt-1,-1,-1):
			globalInfo={}
			for k in globalInfo_src: globalInfo[k]=globalInfo_src[k]
			globalInfo['outputs']={
				'resv0':resv0,
				'resv1':resv1,
				'resv2':resv2,
			}
			globalInfo['initPrices']=initPrices[:]
			t=multiprocessing.Process(
				target=doTests,
				args=(globalInfo,starts[i],starts[i+1],),
				#kwargs=None,
				daemon=True,
			)
			threads.append(t,)
			print(i,starts[i+1]-starts[i],starts[i])
		for t in threads:
			t.start()
			print('thread start:',t,)
		for t in threads: t.join()
	else:
		globalInfo={}
		for k in globalInfo_src: globalInfo[k]=globalInfo_src[k]
		globalInfo['outputs']=None
		resv0,resv1,resv2=doTests(globalInfo,0,simsRound)
	resv0=[x for x in resv0 if x]
	resv1=[x for x in resv1 if x]
	resv2=[x for x in resv2 if x]
	print('len',len(resv0),len(resv1),len(resv2),)
	print('resv0')
	printResv(resv0)
	print('resv1')
	printResv(resv1)
	print('resv2')
	printResv(resv2)
	pass
	print('balancingThreshold',balancingThreshold)
	print('rebalancedRatio',rebalancedRatio)
	print('buyAdjRatio',buyAdjRatio)
	pass


def main(argv):
	t0=time.time()
	doTests_threading(argv)
	t1=time.time()
	print('time',t1-t0)


if __name__=='__main__':
	main(sys.argv)

