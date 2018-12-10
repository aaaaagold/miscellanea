#!/bin/sh
periodTime="11" # in seconds
extIpLookupURL="" # an url prints your ip in plaintext
logFile="ipLogs.txt"
ipPrev="tmp-ip-prev.txt"
ipCurr="tmp-ip-curr.txt"
touch ${logFile}
touch ${ipPrev}
echo "start logging"
echo "log file: ${logFile}"
while [ 0 == 0 ] ;
do
	sleep ${periodTime}
	curl -s --fail ${extIpLookupURL} > ${ipCurr}
	rtv="$?"
	if [ "${rtv}" != "0" ] ; then
		echo "curl fails @ `date`"
		continue
	fi
	diff ${ipPrev} ${ipCurr} > /dev/null && continue
	
	currtime=`date`
	echo "different @ ${currtime}"
	echo "`cat ${ipPrev}` -> `cat ${ipCurr}`"
	cp ${ipCurr} ${ipPrev}
	
	echo ${currtime} >> ${logFile}
	cat ${ipCurr} >> ${logFile}
	echo "" >> ${logFile}
	echo "#" >> ${logFile}
done
