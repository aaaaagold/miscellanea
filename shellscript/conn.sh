#!/bin/sh
while [ 1 ]
do
	date
	echo "try"
	ssh z@hostname -p port -NR remotePort:localIp:localPort -o "ExitOnForwardFailure yes"
	date
	echo "disconnected"
	sleep 111 || exit
done
