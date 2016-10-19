import scripts.lambda_function.main
import sys
import json

event=json.loads(sys.argv[1])
context={}
print scripts.lambda_function.main.lambda_handler(event,context)
