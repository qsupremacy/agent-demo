#!/bin/bash

for i in $(seq 1 100); do
  SESSION_ID=haolipeng
  start=$(date +%s%3N)
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting request $(printf '%3d' "$i") (session: $SESSION_ID)"
  
  agentarts invoke '{"message": "你好"}'  --session $SESSION_ID

  end=$(date +%s%3N)
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished request $(printf '%3d' "$i") (session: $SESSION_ID) - elapsed: $((end - start)) ms"  #--session-id 0cf0f627-baee-4e36-a302-b7f58e44da9c &
  if (( i % 5 == 0 )); then
    wait
  fi
done
wait
