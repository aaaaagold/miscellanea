#!/bin/python3

import sys
import io
import re
import gzip
from urllib import request as r
import http.client


HTTP_PORT=80
HTTPS_PORT=443

scheme2port={
"http":HTTP_PORT,
"https":HTTPS_PORT,
}
scheme2conn={
"http":http.client.HTTPConnection,
"https":http.client.HTTPSConnection,
}

isShowingHeaders= '--show-header' in sys.argv or '--show-headers' in sys.argv 


def ParseUrl(url):
	# return host,path,port
	m_scheme=re.search(r'^(https?):',url)
	host,path,port,conn='','',0,None
	if m_scheme:
		scheme=m_scheme.group(1)
		port=scheme2port[scheme]
		conn=scheme2conn[scheme]
		
		idx0=0
		for i in range(len(m_scheme.group(0)),len(url)):
			if url[i]!='/':
				idx0=i
				break
		idx1=url.find('/',idx0)
		host=url[idx0] if idx1<0 else url[idx0:idx1]
		path='' if idx1<0 else url[idx1:]
	
	return host,path,port,conn


def Req(host,port,path,Conn,cookies={}):
	#return
	rtv=None
	headers={
		"Content-type": "application/x-www-form-urlencoded",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
		"Accept-Encoding": "gzip, deflate",
		"Accept-Language": "en",
		"Cache-Control": "max-age=0",
		
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
	}
	cookieStr=''
	for k in cookies:
		if cookieStr: cookieStr+='; '
		if cookies[k]==True: cookieStr+=k
		else:
			cookieStr+=k
			cookieStr+='='
			cookieStr+=cookies[k]
	if cookieStr: headers['cookie']=cookieStr
	conn=Conn(host,port)
	conn.request("GET", path, None, headers)
	response=conn.getresponse()
	h=response.getheaders()
	if isShowingHeaders:
		print(response.status,response.reason)
		print(h)
	responseHeaders={}
	for p in h: responseHeaders[p[0]]=p[1]
	
	data=response.read()
	conn.close()
	if 'content-encoding' in responseHeaders and responseHeaders['content-encoding']=='gzip':
		data=gzip.GzipFile(fileobj=io.BytesIO(data)).read()
	if isShowingHeaders:
		print(data)
	
	if response.status==301 or response.status==302:
		if 'set-cookie' in responseHeaders:
			newCookieStr=responseHeaders['set-cookie']
			newCookies=re.split(r';[ ]*',newCookieStr)
			for newCookie in newCookies:
				idx=newCookie.find('=')
				if idx<0: cookies[newCookie]=True
				else: cookies[newCookie[0:idx]]=newCookie[idx+1:]
		if 'location' in responseHeaders:
			rtv=responseHeaders['location']
	else: sys.stdout.buffer.write(data)
	return rtv


def main(argv):
	url=argv[1]
	cookies={}
	while True:
		parsedUrl=ParseUrl(url)
		host,path,port,conn=parsedUrl
		if isShowingHeaders:
			for x in parsedUrl: print(x)
		if port:
			res=Req(host,port,path,conn,cookies)
			if not res: break
			url=res
		else: break


if __name__=='__main__':
	main(sys.argv)

