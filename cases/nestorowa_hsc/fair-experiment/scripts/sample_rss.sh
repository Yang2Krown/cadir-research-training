#!/bin/sh
# Only measurement; no termination, filtering, or scientific processing.
pid=$1
sentinel=$2
while [ -e "$sentinel" ] && [ -r "/proc/$pid/status" ]; do
 awk '/^VmRSS:/{print $2}' "/proc/$pid/status"
 sleep 0.05
done
