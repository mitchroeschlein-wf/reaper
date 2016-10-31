#!/bin/bash 
action='{"action": "create", "repository": "https://github.com/mitchroeschlein-wf/linking-api", "service": "linking-api-dev", "tag": "0.5.10-cf"}'
python runlocal.py "$action"

