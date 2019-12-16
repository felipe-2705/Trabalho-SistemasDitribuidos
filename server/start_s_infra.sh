#!/bin/bash

servers=(24) # 4*nro de servers*2(porta pysycn e grpc)
replicas=(2)
port=(11900) # porta base

for i in $(seq 1 8 $servers);
do
	s0=$(($port + $i + 0)) #(grpc 0 , sync 1)
	s1=$(($port + $i + 2)) #(grpc 2 , sync 3)
	s2=$(($port + $i + 4)) #(grpc 4 , sync 5)
	s3=$(($port + $i + 6)) #(grpc 6 , sync 7)
	gnome-terminal -e "bash -c 'python3 Server.py $replicas localhost $s0 localhost $s1 localhost $s2 localhost $s3'"
	gnome-terminal -e "bash -c 'python3 Server.py $replicas localhost $s1 localhost $s0 localhost $s2 localhost $s3'"
#	gnome-terminal -e "bash -c 'python3 Server.py $replicas localhost $s2 localhost $s1 localhost $s0 localhost $s3'"
#	gnome-terminal -e "bash -c 'python3 Server.py $replicas localhost $s3 localhost $s1 localhost $s2 localhost $s0'"
	break
done
