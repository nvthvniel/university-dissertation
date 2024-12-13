import logging, boto3, json, datetime, hashlib

class put_object:

    def __init__ (self, __bucket_name, __data):
        self.bucket_name = __bucket_name
        self.data = __data
    
    # Authenticate to AWS
    def create_client(self):
        logging.info(f"\n[+] Authenticating To AWS ...")

        client = boto3.client('s3')

        return client

    # Store data entry in dynamodb
    def aws_put_object(self, client):
        logging.info(f"\n[+] Storing Log ...")

        file_id = f"{self.data}".encode("utf-8")
        file_id = hashlib.sha256(file_id).hexdigest()

        now = datetime.datetime.now()

        file_name = f"{self.data['metadata']['date'].replace('-', '/')}/{self.data['metadata']['time'].replace(':', '_')}_{file_id}.json"

        response = client.put_object(
            Body = json.dumps(self.data),
            Bucket = f"{self.bucket_name}",
            Key = file_name
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if (response_code != 200):
            print(f" | Error: {response}")
        
        else:
            logging.info(f" | Completed: {file_name}")


        return response_code

    def main(self):
        client = self.create_client()
        response_code = self.aws_put_object(client)

        return response_code