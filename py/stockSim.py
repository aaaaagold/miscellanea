
import sys
import math
import random
from decimal import Decimal, Context, getcontext, localcontext

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
N=1
balancingThreshold=1.0/8/N # p: 1/8 -> 1/8-1/32 ; th: +- 1/8
rebalancedRatio=Decimal(1.0/8-1.0/32)/N
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


def doTest1(argv):
	prices=initPrices[:]
	prices0=prices[:]
	shares=[0]*len(prices)
	cash=initCash
	if 1:
		cash1=int(initCash*(1-cashRate)/len(prices))
		for i in range(len(prices)):
			share=int(cash1/prices[i])
			shares[i]+=share
			cash-=share*prices[i]
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
				if 0<adjSs[i]: adjSs[i]=int(adjSs[i])
			cash-=adjSs[i]*prices[i]
			shares[i]+=adjSs[i]
			r=1+balancingThreshold if adjSs[i]<0 else 1/(1+balancingThreshold)
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
		with localcontext() as ctx:
			ctx.prec=printPrec
			print('round',_,
				resV.to_eng_string(),
				resV0.to_eng_string(),
				(resV/resV0).to_eng_string(),
				(resV/initCash).to_eng_string(),
				(resV-resV0).to_eng_string(),
				(resV-initCash).to_eng_string(),
			'',end='\r')
			pass
		pass
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
	print('resV/resV0',resV/resV0)
	print('resV/initCash',resV/initCash)
	pass
	return [
		float(resV0/initCash),
		float(resV/initCash),
	]
	pass


def printResv(resv):
	resv.sort()
	s=sum(resv)
	m=resv[len(resv)>>1] if len(resv)&1 else (resv[len(resv)>>1]+(resv[(len(resv)>>1)-1]))/2.0
	pprint({
		'mid':m,
		'avg':s/len(resv),
		'min':min(resv),
		'max':max(resv),
	})

def doTests(argv):
	resv0=[]
	resv1=[]
	for i in range(simsRound):
		try:
			res=doTest1(argv)
			resv0.append(res[0])
			resv1.append(res[1])
		except KeyboardInterrupt as e:
			raise e
		except:
			print('broke')
		print(i+1,'/',simsRound)
	print('resv0')
	printResv(resv0)
	print('resv1')
	printResv(resv1)


def main(argv):
	doTests(argv)


if __name__=='__main__':
	main(sys.argv)


