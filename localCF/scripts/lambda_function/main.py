import git_handler
import json
import botocore
import stack_handler
import config_handler
import logging
from settings import github_token, dynamodb_region, dynamodb_table
from jinja2 import Environment, FunctionLoader, meta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper function to aid in extracting variables from template. There's
# probably a much better way to do this.


def getSource(template):

    return template


def handleError(message):

    logger.error(message)
    output = {}
    output['Status'] = "ERROR"
    output['Message'] = message
    return output


def checkStackStatus(event):

    service = event['service']
    repo = event['repository']
    tag = event['tag']
    tagRef = "refs/tags/" + tag
    repostr = repo + ":" + tag

    # Initialize the git handler object
    try:
        git = git_handler.git_handler(github_token)
    except:
        message = "Could not initialize github handler object using provided token"
        logger.error(message)

        return [{
            "StackId": "unknown",
            "Status": "ERROR",
            "Message": message
        }]

    # Grab the deploy configuration file from the repo
    try:
        deployConfig = json.loads(git.get_file_content(
            repo, tagRef, "deploy.json"))
    except:
        message = "Could not retrieve deploy.json from github and parse it as json"
        logger.error(message)

        return [{
            "StackId": "unknown",
            "Status": "ERROR",
            "Message": message
        }]

    serviceConfig = deployConfig[service]
    output = []
    # For each stack in the service, get a dict representing its status
    for stackConfig in serviceConfig:
        stackId = stackConfig['stackId']
        region = stackConfig['region']
        try:
            stackStatus = stack_handler.check_stack(stackId, region, repostr)
            output.append(stackStatus)
        except:
            message = (
                "An error occured when checking the status of %s" % stackId)
            logger.error(message)
            stackStatus = {}
            stackStatus['StackId'] = stackId
            stackStatus['Status'] = "ERROR"
            stackStatus['Message'] = message
            output.append(stackStatus)

    return output


def deleteStacks(event):

    repo = event['repository']
    service = event['service']
    tag = event['tag']

    repostr = repo + ":" + tag
    tagRef = "refs/tags/" + tag

    # Initialize the git handler object
    try:
        git = git_handler.git_handler(github_token)
    except:
        return handleError(
            "Could not authenticate with github using provided token")

    # Grab the deploy configuration file from the repo
    try:
        deployConfig = json.loads(git.get_file_content(
            repo, tagRef, "deploy.json"))
    except:
        return handleError(
            "Could not retrieve deploy.json from github and parse it as json")

    serviceConfig = deployConfig[service]
    for stackConfig in serviceConfig:
        stackId = stackConfig['stackId']
        region = stackConfig['region']
        try:
            stack_handler.delete_stack(stackId, region)
        except:
            return handleError(
                "Could not delete stack %s" % stackId)
    output = {}
    output['Status'] = "SUCCESS"
    output['Message'] = "Successfully deleted all requested stacks"
    return output


def updateStacks(event):

    # Get parameters from event
    action = event['action']
    # github repository name
    repo = event['repository']
    # service is used in the .deploy configuration file in the repository.
    # region is also used to identify the region to deploy the cloudformation
    # stack to
    service = event['service']
    # Tag is the tag name in the github repo to use to get the stack files from
    tag = event['tag']

    repostr = repo + ":" + tag
    tagRef = "refs/tags/" + tag

    # Initialize the git handler object
    try:
        git = git_handler.git_handler(github_token)
    except:
        return handleError(
            "Could not authenticate with github using provided token")

    # Initialize the config handler object that will be responsible for
    # retrieving per
    # stack configuration
    configReader = config_handler.config_handler(
        dynamodb_table, dynamodb_region)

    # Grab the deploy configuration file from the repo
    try:
        deployConfig = json.loads(git.get_file_content(
            repo, tagRef, "deploy.json"))
    except:
        return handleError(
            "Could not retrieve deploy.json from github and parse it as json")

    serviceConfig = deployConfig[service]
    for stackConfig in serviceConfig:
        # Determine template and parameters file locations from config
        stackId = stackConfig['stackId']
        templateLocation = stackConfig['template']
        parameterLocation = stackConfig['parameters']
        region = stackConfig['region']
        # Get policy for this stack change if it's included
        stackPolicyLocation = stackConfig['stackPolicy']
        # Grab the contents of the stack policy file from the repository
        try:
            stackPolicy = git.get_file_content(repo, tagRef, stackPolicyLocation)
        except:
            return handleError(
                "Could not get stack policy file %s from github repo %s tagged %s"
                % (stackPolicyLocation, repo, tagRef))
        # Get policy for this stack change if it's included
        updatePolicy = ""
        if 'updatePolicy' in stackConfig:
            try:
                updatePolicy = git.get_file_content(repo, tagRef, stackConfig['updatePolicy'])
            except:
                return handleError(
                    "Could not get update policy file %s from github repo %s tagged %s"
                    % (stackConfig['updatePolicy'], repo, tagRef))

        # Grab the contents of the template and parameters from the repository
        try:
            templateBody = git.get_file_content(repo, tagRef, templateLocation)
        except:
            return handleError(
                "Could not get template file %s from github repo %s tagged %s"
                % (templateLocation, repo, tagRef))
        try:
            parameterTemplate = git.get_file_content(
                repo, tagRef, parameterLocation)
        except:
            return handleError(
                "Could not get parameter file %s from github repo %s tagged %s"
                % (parameterLocation, repo, tagRef))

        # Get a list of jinja2 variables in the parameter template
        try:
            env = Environment(loader=FunctionLoader(getSource))
            template_source = env.loader.get_source(env, parameterTemplate)[0]
            parsed_content = env.parse(template_source)
            variableList = meta.find_undeclared_variables(parsed_content)
        except:
            return handleError(
                "Could not parse parameters template for stack %s" % stackId)

        # Get the keys of the variables templated in the parameters file
        # from the dynamodb table
        variableDict = {}
        for variable in variableList:
            try:
                message = configReader.ReadMessage(variable)
            except:
                return handleError(
                    "Could not find value for variable %s in stack %s"
                    % (variable, stackId))

            variableDict[variable] = message

        # Apply the variables to the templated parameters file and attempt
        # to parse the result as JSON
        try:
            parameterArgs = json.loads(
                env.get_template(parameterTemplate).render(variableDict))
        except:
            return handleError(
                "Could not parse templated parameters file as json")
        if action == "create":
            try:
                result = stack_handler.create_stack(
                    stackId, templateBody, parameterArgs, region, repostr, stackPolicy)
                logger.info(result)
                logger.info("Successfully created %s in %s" % (
                    stackId, region))
            except botocore.exceptions.ClientError as exc:
                if exc.response['Error']['Code'] == 'ValidationError':
                    return handleError(exc.response['Error']['Message'])
                else:
                    return handleError("Could not submit stack create due to boto error. This is usually because the stack already exists, or due to a communication error with Amazon.")
            except:
                return handleError("Could not submit stack create.")
        elif action == "update":
            try:
                result = stack_handler.update_stack(
                    stackId, templateBody, parameterArgs, region, repostr, stackPolicy, updatePolicy)
                logger.info(result)
                logger.info("Successfully deployed %s in %s" % (
                    stackId, region))
            except botocore.exceptions.ClientError as exc:
                if exc.response['Error']['Code'] == 'ValidationError':
                    if exc.response['Error']['Message'] != "No updates are to be performed.":
                        return handleError(exc.response['Error']['Message'])
                else:
                    return handleError("Could not submit stack update due to boto error.")
            except:
                return handleError("Could not submit stack update.")

    output = {}
    output['Status'] = "SUCCESS"
    output['Message'] = "Successfully deployed all stack creates and updates"
    return output


def lambda_handler(event, context):

    action = event['action']

    if action == "update" or action == "create":
        return updateStacks(event)
    if action == "delete":
        return deleteStacks(event)
    elif action == "status":
        return checkStackStatus(event)
    else:
        return handleError("Action '%s' not supported" % action)
