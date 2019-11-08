#!/bin/bash

ids=(2 7 12 15)

for i in ${ids[*]} 
do
	port=$(($i + 11910))
	gnome-terminal -e "bash -c 'python3 Server.py $port;sleep 3'"
done
