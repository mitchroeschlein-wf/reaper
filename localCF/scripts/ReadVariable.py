#!/usr/bin/env python
from lambda_function import config_handler
from lambda_function.settings import dynamodb_region, dynamodb_table
import argparse
import json

parser = argparse.ArgumentParser(description="Write a configuration variable to the cf_deployer_config table")
parser.add_argument('key', metavar='key', type=str, help='variable key name')

args = parser.parse_args()
key = args.key

configObject = config_handler.config_handler(dynamodb_table,dynamodb_region)

print configObject.ReadMessage(key)

