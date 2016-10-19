import boto3
import base64

class config_handler:

    def __init__(self, table, region):
        self.kmsClient = boto3.client('kms', region_name=region)
        dynamodbResource = boto3.resource('dynamodb', region_name=region)
        self.dynamodbTable = dynamodbResource.Table(table)

    def ReadMessage(self, key):
        item = self.dynamodbTable.get_item(
            Key={
                'key':key
            },
        )
        dataBlob = base64.b64decode(item['Item']['data'])
        resp = self.kmsClient.decrypt(CiphertextBlob=dataBlob)
        message = resp['Plaintext']
        return message

    def WriteMessage(self, key, message, kmsKeyARN):
        resp = self.kmsClient.encrypt(KeyId=kmsKeyARN, Plaintext=message)
        dataBlob = base64.b64encode(resp['CiphertextBlob'])
        self.dynamodbTable.put_item(
            Item={
                'key':key,
                'data':dataBlob
            }
        )
        return
