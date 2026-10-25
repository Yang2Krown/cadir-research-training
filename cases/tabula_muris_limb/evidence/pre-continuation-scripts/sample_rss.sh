#!/usr/bin/env sh
# Sample the actual inner-container R process, not the Docker client.
# Exit on parent death even when a failed run leaves its sentinel behind.
while [ -e "$2" ]; do
  awk '/^VmRSS:/ {print $2}' "/proc/$1/status" 2>/dev/null || break
  sleep 0.05
done
