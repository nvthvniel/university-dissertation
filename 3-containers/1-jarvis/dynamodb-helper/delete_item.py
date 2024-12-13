import logging, boto3

class delete_item:

    def __init__ (self, __table_name, __callback_id):
        self.table_name = __table_name
        self.callback_id = __callback_id
    
    # Authenticate to AWS
    def create_client(self):
        logging.info(f"\n[+] Authenticating To AWS ...")

        client = boto3.client('dynamodb')

        return client

    # Retrieve data entry from dynamodb
    def aws_delete_item(self, client):
        logging.info(f"\n[+] Deleting Data ...")

        response = client.delete_item(
            TableName = self.table_name,
            Key = {
                "callback_id": { "S": self.callback_id }
            }
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        response_data = None

        if (response_code != 200):
            print(f" | Error: {response}")
        
        else:
            logging.info(f" | Completed")

        return response_code

    def main(self):
        client = self.create_client()
        response_code = self.aws_delete_item(client)

        return response_code