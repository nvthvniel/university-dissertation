import logging, boto3

class put_item:

    def __init__ (self, __table_name, __body):
        self.table_name = __table_name
        self.body = __body
    
    # Authenticate to AWS
    def create_client(self):
        logging.info(f"\n[+] Authenticating To AWS ...")

        client = boto3.client('dynamodb')

        return client

    # Store data entry in dynamodb
    def aws_put_item(self, client):
        logging.info(f"\n[+] Storing Data ...")

        items = {}

        for key in self.body.keys():
            items[key] = { "S": str(self.body[key]) }

        response = client.put_item(
            TableName = self.table_name,
            Item = items
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if (response_code != 200):
            print(f" | Error: {response}")
        
        else:
            logging.info(f" | Completed")


        return response_code

    def main(self):
        client = self.create_client()
        response_code = self.aws_put_item(client)

        return response_code