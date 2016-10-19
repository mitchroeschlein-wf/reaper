import boto3

def delete_stack(stackName, region):

    args = {}
    args['StackName'] = stackName

    session = boto3.session.Session(region_name=region)
    client = session.client('cloudformation')
    client.delete_stack(**args)

    # Construct the output based on the information gathered above
    output = {}
    output['StackId'] = stackName
    output['Message'] = "Deleted stack %s" % stackName
    output['Status'] = "SUCCESS"
    return output


def update_stack(stackName, templateBody, parameterArgs, region, repostr, stackPolicy, updatePolicy):

    args = {}
    args['StackName'] = stackName
    args['TemplateBody'] = templateBody
    args['StackPolicyBody'] = stackPolicy
    if updatePolicy != "":
        args['StackPolicyDuringUpdateBody'] = updatePolicy
    args['Capabilities'] = [ 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM' ]
    args['Parameters'] = parameterArgs
    args['Tags'] = [ { "Key": "Repository", "Value": repostr } ]

    session = boto3.session.Session(region_name=region)
    client = session.client('cloudformation')
    client.update_stack(**args)
    return True

def create_stack(stackName, templateBody, parameterArgs, region, repostr, stackPolicy):

    args = {}
    args['StackName'] = stackName
    args['TemplateBody'] = templateBody
    args['StackPolicyBody'] = stackPolicy
    args['Capabilities'] = [ 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM' ]
    args['Parameters'] = parameterArgs
    args['Tags'] = [ { "Key": "Repository", "Value": repostr } ]
    
    session = boto3.session.Session(region_name=region)
    client = session.client('cloudformation')
    client.create_stack(**args)
    return True


# This function will check two things:
# 1. That the stack Repository tag matches a desired value
# 2. If the state of the update is complete, updating, or failed
#
#  * If either of the conditions fails the function will return ERROR
#  * If the tags are correct but the status is updating, then the
# function will return UPDATING
#  * If the tags are correct and the status is complete, then the
# function will return SUCCESS

def check_stack(stackName, region, repostr):

    # Get the information on the stack using boto
    session = boto3.session.Session(region_name=region)
    client = session.client('cloudformation')
    stackInfo = client.describe_stacks(
        StackName=stackName
    )
    stackStatusMessage = stackInfo['Stacks'][0]['StackStatus']
    stackTags = stackInfo['Stacks'][0]['Tags']

    # Determine if the repository given matches the stack
    # There are three cases here:
    # 1. The stack doesn't have a Repository tag
    # 2. The stack has a Repository tag but it doesn't match
    # 3. The stack has a Repository tag and it matches

    repoStatus = False
    repoMessage = ""
    repoTagValue = "NONE"
    for tag in stackTags:
        if tag['Key'] == "Repository":
            repoTagValue = tag['Value']
    if repoTagValue == "NONE":
        repoStatus = False
        repoMessage = "Could not find Repository tag for stack. "
    else:
        if repoTagValue != repostr:
            repoStatus = False
            repoMessage = (
                "Repository tag does not match. Provided: %s, Stack tag: %s. "
                % (repostr, repoTagValue))
        else:
            repoStatus = True
            repoMessage = "Repository tag matches. "

    # Determine if the stack has been successfully updated
    # There are three cases here:
    # 1. The stack has state UPDATE_COMPLETE
    # 2. The stack has one of the UPDATE in progress states
    # 3. The stack is in none of the above states

    stackMessage = ""
    stackSuccess = stackStatusMessage == 'UPDATE_COMPLETE' or stackStatusMessage == 'CREATE_COMPLETE'
    stackUpdating = (
        stackStatusMessage == 'CREATE_IN_PROGRESS' or
        stackStatusMessage == 'UPDATE_IN_PROGRESS' or
        stackStatusMessage == 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS')
    if stackSuccess:
        stackMessage = "Successfully deployed the stack update."
    elif stackUpdating:
        stackMessage = "Stack update still in progress."
    else:
        stackMessage = "Stack update failed."

    # Construct the output based on the information gathered above
    output = {}
    output['StackId'] = stackName
    output['Message'] = repoMessage + stackMessage
    if not repoStatus:
        output['Status'] = "ERROR"
    elif not stackUpdating and not stackSuccess:
        output['Status'] = "ERROR"
    elif not stackSuccess:
        output['Status'] = "UPDATING"
    else:
        output['Status'] = "SUCCESS"
    return output
