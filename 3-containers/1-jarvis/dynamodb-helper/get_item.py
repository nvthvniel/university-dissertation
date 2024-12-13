import logging, boto3

class get_item:

    def __init__ (self, __table_name, __callback_id):
        self.table_name = __table_name
        self.callback_id = __callback_id
    
    # Authenticate to AWS
    def create_client(self):
        logging.info(f"\n[+] Authenticating To AWS ...")

        client = boto3.client('dynamodb')

        return client

    # Retrieve data entry from dynamodb
    def aws_get_item(self, client):
        logging.info(f"\n[+] Getting Data ...")

        response = client.get_item(
            TableName = self.table_name,
            Key={ 
                "callback_id": { "S": str(self.callback_id) }
            }
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        response_data = None

        if (response_code != 200):
            print(f" | Error: {response}")
        
        else:
            try:
                logging.info(f" | Completed")

                keys = response["Item"].keys()

                response_data = {}
                
                for key in keys:
                    response_data[key] = response["Item"][key]["S"]

            
            except KeyError:
                logging.info(f" | No data retrieved, likely re-click")

                response_code = 500

        return response_data, response_code

    def main(self):
        client = self.create_client()
        response_data, response_code = self.aws_get_item(client)

        return response_data, response_code