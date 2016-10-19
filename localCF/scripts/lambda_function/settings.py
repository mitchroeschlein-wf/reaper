from github import Github
import os
import sys

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# suppress github internal logging
github_log = logging.getLogger("github")
github_log.setLevel(logging.WARNING)
github_log.propagate = True
#these are the AWS keys for dev corp and prod
keys = {
    "dev": "arn:aws:kms:us-east-1:663511558366:key/ebc16edf-1e10-4ddf-a025-cadc8fa82785",
    "corp": "arn:aws:kms:us-east-1:138996711548:key/5feeaa01-0a3e-45eb-a85f-b2e65ae9b266",
    "prod": "arn:aws:kms:us-east-1:806289232271:key/dac56c46-a070-4f81-8e42-7bfe1e522da1"
}
dynamodb_region = "us-east-1"
dynamodb_table = "cf_deployer_config"

github_token = None
try:
    # look for GITHUB_TOKEN defined in ~/.ssh/apikeys.py
    sys.path.append(os.path.abspath(os.path.join(os.path.expanduser('~'), '.ssh')))
    from apikeys import GITHUB_TOKEN
    github_token = GITHUB_TOKEN
    logger.debug("Using GITHUB_TOKEN from ~/.ssh/apikeys")
except ImportError:
    pass

if github_token is None:
    try:
        github_token = os.environ['GITHUB_TOKEN']
        logger.debug("Using GITHUB_TOKEN env var")
    except KeyError:
        sys.stderr.write("ERROR: you must either set GITHUB_TOKEN in ~/.ssh/apikeys.py or export it as an env variable.\n")
        raise SystemExit(1)

