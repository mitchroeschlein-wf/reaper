#!/bin/bash 
action='{"action": "create", "repository": "Workiva/example", "service": "aws-config-rule-tagging-dev", "tag": "1.0.0"}'
python runlocal.py "$action"
