#!/bin/bash
function help()
{
	echo "Usage: ./pushCode.sh <function name> <path to code> <config file>"
	exit
}

if [ -z "$1" ]; then
	echo "No function name provided!"
	help
fi
if [ -z "$2" ]; then
	echo "No code path provided!"
	help
fi
if [ -z "$3" ]; then
	echo "No config file provided!"
	help
fi
FUNCTION=$1
CODEPATH=$2
CONFIGFILE=$3
if [ -d "${CODEPATH}" ]; then
	if [ -e "${FUNCTION}.zip" ]; then
		rm ${FUNCTION}.zip
	fi
    cp -r ${CODEPATH} build
    cp $CONFIGFILE build/config.json
	cd build
    pip install -t $(pwd) -r requirements.txt
	zip -r ../${FUNCTION}.zip *
	cd ..
	aws --region=us-east-1 --profile dev lambda update-function-code --function-name ${FUNCTION} --zip-file fileb://${FUNCTION}.zip
else
	echo "Did not find code path directory ${CODEPATH}"
fi
