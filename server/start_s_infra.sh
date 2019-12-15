#!/bin/bash

servers=(24) # 4*nro de servers*2(porta pysycn e grpc)
replicas=(4)
port=(11900) # porta base

for i in $(seq 1 8 $servers);
do
	s0=$(($port + $i + 0))
	s1=$(($port + $i + 2))
	s2=$(($port + $i + 4))
	s3=$(($port + $i + 6))
	gnome-terminal -e "bash -c 'python3 Server.py $replicas 127.0.0.1 $s0 127.0.0.1 $s1 127.0.0.1 $s2 127.0.0.1 $s3'"
done
