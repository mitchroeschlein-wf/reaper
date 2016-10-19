# Cloudformation Deployer

Provides easy to use interface for deploying Cloudformation stacks from github repositories.

## Deploy file (required to use a Git repo with CF Deployer)

A github repo **must** contain a deploy.json file in its root if that repo is intended for use with the CloudFormation Deployer.

The deploy.json file contains deploy parameters which instruct the CF Deployer how to deploy a CloudFormation stack.  

A CloudFormation deployer enabled service is referenced by a service name, which may consist of one or more CloudFormation stacks. 


 - For example, an xbrl-validation service may have stacks in us-east-1
   and us-west-2 that are deployed simultaneously.
 - Example deploy.json file for a service called **example-service-1** containing two stacks, one in us-east-1 and one in us-west-2. 
 - Each stack has four parameters:
   - stackId - The name of the stack in CloudFormation.
   - template - The location of the CloudFormation template file in the git repo
   - parameters - The location of the CloudFormation parameters file in the git repo
   - region - Target AWS Region for service deploy.

```json
{
    "example-service-1": 
    [
        {
            "stackId": "example-stack-east",
            "template": "example-1.json",
            "parameters": "dev/us-east-1/example-east-parameters.json",
            "region": "us-east-1",
            "stackPolicy": "policies/default-stack-policy.json"
        },
        {
            "stackId": "example-stack-west",
            "template": "example-1.json",
            "parameters": "dev/us-west-2/example-west-parameters.json",
            "region": "us-west-2",
            "stackPolicy": "policies/default-stack-policy.json"
        }
    ],

    "example-service-2": 
    [
        {
            "stackId": "example-with-one-stack",
            "template": "example-2.json",
            "parameters": "dev/us-east-1/example-2-parameters.json",
            "region": "us-east-1",
            "stackPolicy": "policies/default-stack-policy.json",
            "updatePolicy": "policies/new-service-stack-policy.json"
        }
    ]
}
```

In the above example, example-service-1 is a service that has two stacks, one in us-east-1 and one in us-west-2. Each stack has four parameters:
- stackId: The name of the stack in Cloudformation.
- template: The location of the cloudformation template file in the git repo
- parameters: The location of the cloudformation parameters file in the git repo
- region: The aws region to do the deploy in
- stackPolicy: The location of the stack policy in the git repo
- updatePolicy: (**Optional**) The location of the stack update policy in the git repo. This policy will only be applied to the updates that have this parameter specified. It will not permanently change the stack policy.

## Secrets

The service stores and retrieves secrets in a simple key-value configuration (values encrypted by KMS) stored in DynamoDB.  Secrets can be used in CloudFormation by enclosing the {{secretpassword}} in double braces. 

```
./WriteVariable dev key value
./ReadVariable key
```

 - The secret **must be uploaded to the DynamoDB table prior to deploying the service**, and this can be done via the **ReadVariable** and **WriteVariable** scripts included in this git repo.  

 - Process flow for securely handling secrets:
1. secrets
2. uploaded to DynamoDB
3. referenced in parameters file
4. read from DynamoDB
5. replaced in the text of the file before being passed on to CloudFormation.

## API Specification:

- API calls will be a POST request to an endpoint requiring an API key specified by the x-api-key header.
- The data payload is a JSON formatted string and will return another JSON formatted string. There are two actions available, **Update** and **Status**. 

### **Create**

Submits the stack creation to cloudformation for each stack in the service specified.

#### Input:

    {
        "action": "create", 
        "repository": "<github repo>", 
        "tag": "<tag name of the repo to deploy>",
        "service": "<service name in the deploy.json file to perform the stack update on>"
    }

#### Result:

    {
        "Status": "SUCCESS", 
        "Message": "Successfully deployed all stack updates"
    }

The result will consist of two values:
- Status: One of SUCCESS or ERROR, depending on the success of the create api call
- Message: A text description of the create result

### Update

Submits the stack update to cloudformation for each stack in the service specified.

#### Input:

    {
        "action": "update", 
        "repository": "<github repo>", 
        "tag": "<tag name of the repo to deploy>"
        "service": "<service name in the deploy.json file to perform the stack update on>"
    }

#### Result

    {
        "Status": "SUCCESS", 
        "Message": "Successfully deployed all stack updates"
    }

The result will consist of two values:
- **Status** One of SUCCESS or ERROR, depending on the success of the update
- **Message** A text description of the update result

### Delete

Submits the stack update to cloudformation for each stack in the service specified.

#### Input:

    {
        "action": "delete", 
        "repository": "<github repo>", 
        "tag": "<tag name of the repo to deploy>"
        "service": "<service name in the deploy.json file to perform the stack update on>"
    }

#### Result

    {
        "Status": "SUCCESS", 
        "Message": "Successfully deleted requested stacks"
    }

The result will consist of two values:
- **Status** One of SUCCESS or ERROR, depending on the success of the deletion
- **Message** A text description of the delete result

### **Status**

Check the status of a deploy. 
Stack is in the current state of the CloudFormation deploy process and that the specified git repo and tag are what's currently deployed. All parameters are required.

#### Input:

    {
        "action": "status", 
        "repository": "<github repo>", 
        "tag": "<tag name of the repo to check>",
        "service": "<service name in the deploy.json file to check>"
    }

#### Result:

    [
        {
            "StackId": "example-stack-east",
            "Status": "SUCCESS",
            "Message": "Repository tag matches. Successfully deployed the stack update."
        }, 
        {
            "StackId": "example-stack-west", 
            "Status": "SUCCESS", 
            "Message": "Repository tag matches. Successfully deployed the stack update."
        }
    ]

The result will consist of a list of results for each stack in the service. Each stack will return three values:
 - **StackId**: The name of the stack
 - **Status**: SUCCESS, UPDATING, or ERROR, depending on the current state of the stack
 - **Message**: A text description of the state


## Deploying using the API

Deploying should follow the following pattern

1. Submit an update request to the API using the update API call.
 
 **ERROR**: the deploy has failed.  Contact the on-call Operations Engineer.

 **SUCCESS**: The status returns SUCCESS, continue to the next step.

1. Check the status of the service using the status API call.

 **The status of ALL services is SUCCESS**: the deploy is successful.

 **The status of ALL services is SUCCESS or UPDATING**: the deploy is still in progress. Recheck status after a brief delay.

 **The status of ANY service is ERROR**: the deploy has failed. Contact the on-call Operations Engineer.


## Running locally

You can run the cloudformation deployer locally for testing and development. 

First, install the appropriate python [requirements](https://github.com/Workiva/cloudformation_deployer/blob/master/scripts/lambda_function/requirements.txt).

**Note**:  If you have not already, please set up your GITHUB_TOKEN in ~/.ssh/apikeys.py, or set your GITHUB_TOKEN environment variable in order to communicate with github

run_local.py takes one argument, the json formatted string that would be passed to the API

run_local.sh has an example of how one might use run_local.py

## Using cloudformation to create the service

   aws cloudformation create-stack \
        --region us-east-1 \
        --stack-name cf-deployer-corp \
        --template-body file://$(pwd)/cf_deployer.json \
        --parameters file://$(pwd)/corp/us-east-1/cf_deployer-corp-parameters.json \
        --stack-policy-body file:///$(pwd)/policies/default-stack-policy.json \
        --capabilities CAPABILITY_IAM

   aws cloudformation create-stack \
        --region us-east-1 \
        --stack-name cf-deployer-prod \
        --template-body file://$(pwd)/cf_deployer.json \
        --parameters file://$(pwd)/prod/us-east-1/cf_deployer-prod-parameters.json \
        --stack-policy-body file:///$(pwd)/policies/default-stack-policy.json \
        --capabilities CAPABILITY_IAM
