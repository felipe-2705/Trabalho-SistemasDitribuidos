#!/bin/bash

servers=(12) # 4*nro de servers
replicas=(4)
port=(11900) # porta base

for i in $(seq 1 4 $servers);
do
	s0=$(($port + $i + 0))
	s1=$(($port + $i + 1))
	s2=$(($port + $i + 2))
	s3=$(($port + $i + 3))
	gnome-terminal -e "bash -c 'python3 Server.py $replicas 127.0.0.1 $s0 127.0.0.1 $s1 127.0.0.1 $s2 127.0.0.1 $s3'"
#	gnome-terminal -e "bash -c 'sleep 3;python3 Server.py $replicas 127.0.0.1 $s0 127.0.0.1 $s1 127.0.0.1 $s2 127.0.0.1 $s3'"
	break
done

#ids=(2 7 12 15) 
#
#for i in ${ids[*]} 
#do
#	port=$(($i + 11910))
#	gnome-terminal -e "bash -c 'sleep 3;python3 Server.py $port'"
#done
