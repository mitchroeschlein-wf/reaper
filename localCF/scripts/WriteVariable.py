#!/usr/bin/env python
from lambda_function import config_handler
from lambda_function.settings import dynamodb_region, dynamodb_table, keys
import argparse
import json

parser = argparse.ArgumentParser(description="Write a configuration variable to the cf_deployer_config table")
parser.add_argument('account', metavar='account', type=str, help='account name (dev/corp/prod)')
parser.add_argument('key', metavar='key', type=str, help='variable key name')
parser.add_argument('value', metavar='value', type=str, help='variable value')


args = parser.parse_args()
account = args.account
key = args.key
value = args.value

kmsKeyARN = keys[account]

configObject = config_handler.config_handler(dynamodb_table,dynamodb_region)

configObject.WriteMessage(key, value, kmsKeyARN)
