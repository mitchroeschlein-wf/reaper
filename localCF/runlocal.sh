#!/bin/bash 
action='{"action": "create", "repository": "mitchroeschlein-wf/linking-api", "service": "linking-api-dev", "tag": " 0.5.10-cf"}'
python runlocal.py "$action"
