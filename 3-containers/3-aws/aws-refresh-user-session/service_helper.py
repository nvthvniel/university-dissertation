import boto3, botocore, requests, logging, json, hashlib, os, datetime

class service_helper:

    # Constructor
    def __init__ (self, __require_approval, __approvers, __channel_id, __user_id, __thread_id, __arguments):
        self.require_approval = __require_approval
        self.approvers = __approvers
        self.arguments = __arguments
        self.channel_id = __channel_id
        self.user_id = __user_id
        self.thread_id = __thread_id

        self.service_name = os.getenv("K_SERVICE")

    def send_response(self, attachments, text = ""):
        logging.info("\n[+] Sending Slack Response ...")
        # logging.info(f" | Text: {text}")
        # logging.info(f" | Attachements: {attachments}")

        payload = {
            "channel": self.channel_id,
            "thread_ts": self.thread_id,
            "text": text,
            "attachments": attachments
        }

        json_to_send = {"method": "chat.postMessage", "payload": payload}

        response = requests.post("http://helper.slack.svc.cluster.local", json=json_to_send)
        response = json.loads(response.text)

        if (response["ok"] != True):
            logging.info(f" | Error: {response}")

    def send_error_message(self, message):

        attachments_text = f"*Error*\n*- Service Name:* {self.service_name}\n*- Message:* {message}"
            
        attachments = [{"text": attachments_text, "color": "#FF7369"}]
        self.send_response(attachments)

    # Get username from slack user ID
    def get_username(self, user_id):
        logging.info("\n[+] Getting Slack User's Profile ...")
        logging.info(f" | User ID: {user_id}")

        email = None

        payload = {
            "user": user_id
        }

        response = requests.post("http://helper.slack.svc.cluster.local", json={"method": "users.profile.get", "payload": payload})
        logging.info(f" | Response: {response}")

        response = json.loads(response.text)

        if (response["ok"] != True):
            logging.info(f" | Error: {response['error']}")

            self.send_error_message(f"Couldn't resolve user's email via Slack API: {response['error']}")
        
        else:
            email = response["profile"]["email"]

        return email

     # Extract data from user's command
    
    # Get slack user ID from email
    def get_userid(self):
        logging.info("\n[+] Getting Approvers' Slack ID ...")

        users = []

        for username in self.approvers:

            payload = {
                "email": username
            }

            response = requests.post("http://helper.slack.svc.cluster.local", json={"method": "users.lookupByEmail", "payload": payload})

            response = json.loads(response.text)

            try:
                user_id = response["user"]["id"]
                users.append(user_id)

                logging.info(f" | {username}: {user_id}")
            
            # Couldn't get slack user ID from username (user doesn't exist in workspace)
            except KeyError:
                logging.info(f" | Error: Couldn't Get {username}'s Slack ID, likely doesn't exist in Slack workspace")

                self.send_error_message(f"Couldn't Get approver '{username}'s Slack ID")
        
        return users

    def extract_payload(self, user_prompt, arguments):
        logging.info("\n[+] Extracting Data From Payload ...")

        payload = {}

        user_prompt = user_prompt.split(" ")

        for argument in arguments:

            flag = argument.split("=")[0]
            datatype = argument.split("=")[1]

            index = user_prompt.index(flag) + 1
            value = user_prompt[index]

            if (datatype == "list"):
                value = value.split(",")
            
            elif (datatype == "string"):
                value = str(value)

            elif (datatype == "integer"):
                value = int(value)
            
            elif (datatype == "boolean"):
                value = bool(value)
            
            elif (datatype == "float"):
                value = float(value)

            payload[flag] = value
            logging.info(f" | {flag}: {value}")
    
        return payload
    
    # Authenticate to AWS, create client in specific region
    def create_session(self, region, account_id, email):
        logging.info(f"\n[+] Authenticating To AWS ...")

        role_arn = f"arn:aws:iam::{account_id}:role/jarvis-incident-response"
        client = boto3.client('sts')

        session = None

        try:
            response = client.assume_role(RoleArn=role_arn, RoleSessionName=f"jarvis-incident-response-{email}")
            temp_credentials = response['Credentials']

            session = boto3.Session(
                    aws_access_key_id=temp_credentials['AccessKeyId'],
                    aws_secret_access_key=temp_credentials['SecretAccessKey'],
                    aws_session_token=temp_credentials['SessionToken'],
                    region_name=region
            )

            logging.info(f" | Created session 'jarvis-automation-{email}' in {account_id}")
        
        except botocore.exceptions.ClientError:
            logging.info(f" | Error: couldn't assume role, sending error message ...")

            self.send_error_message(f"Couldn't assume role: '{role_arn}'")


        return session

    # Check job-scope + resource-scope approval requirement
    def check_approval_scope(self, tags):
        logging.info("\n[+] Checking If Approval Is Required ...")

        approval_requirements = {}
        
        if (self.require_approval == True):
            logging.info(f" | Approval required via service scope")
            
            for instance_id in tags.keys():
                approval_requirements[instance_id] = True


        # dict = {resource_id: [{"key": "name", "value": "demo"}, {"jarvis-approval-required", "false", ...}]}
        else:
            for resource_id in tags.keys():

                resource_tags = tags[resource_id]

                if (resource_tags != None):

                    for tag_pair in resource_tags:
                        tag_key = tag_pair["Key"].lower()
                        tag_value = tag_pair["Value"].lower()

                        if ( (tag_key == "jarvis-approval-required") and (tag_value == "true") ):
                            logging.info(f" | Approval required via tag scope, resource ID: {resource_id}")
                            approval_requirements[resource_id] = True
                

                if (resource_id not in approval_requirements.keys()):
                    logging.info(f" | Approval not required")
                    approval_requirements[resource_id] = False
        
        return approval_requirements
    
    def validate_approver_response(self, response, callback_id, approver_user_id, users):
        valid = False

        # Valid approver clicked approve
        if ( (response == "approved") and (approver_user_id in users) ):
            logging.info(f" | Valid approver clicked '{response}', commiting action ...")

            deleted = self.delete_approval_request(callback_id)

            if (deleted == True):
                valid = True

                attachments_text = f"*<@{approver_user_id.upper()}> approved this request*"
                
                attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
                self.send_response(attachments)
            
            else:
                logging.info(" | Error: couldn't delete approval request entry")

                self.send_error_message("couldn't delete entry in dynamodb, check service's logs for more information")

        # Valid approver click not approved
        elif ( (response == "not_approved") and (approver_user_id in users) ):
            # delete from dynamodb
            deleted = self.delete_approval_request(callback_id)

            if (deleted == True):

                logging.info(f" | Valid approver clicked '{response}', sending acknowledgment ...")

                attachments_text = f"*Warning:* <@{approver_user_id}> clicked *Not Approved*.\nThis action will not be commited"
                
                attachments = [{"text": attachments_text, "color": "#FFA344"}]
                self.send_response(attachments)
            
            else:
                logging.info(" | Error: couldn't delete approval request entry")

                self.send_error_message("couldn't delete entry in dynamodb, check service's logs for more information")

        
        # Invalid approver clicked not approved
        elif (approver_user_id not in users):
            logging.info(f" | Error: User isn't in approvers list, sending error message")

            error_message = f"<@{approver_user_id.upper()}> isn't in approvers list"

            self.send_error_message(error_message)
        
        else:
            logging.info(f" | Error: Unhandled situation. Response = {response} & User = {approver_user_id} / {users}")

            self.send_error_message(f"Unhandled validate_approver_response situation. Response = {response} & User = {approver_user_id} / {users}")
        
        return valid

    def generate_callback_id(self, target):
        callback_id = f"{self.thread_id}{target}"
        callback_id = callback_id.encode("utf-8")
        callback_id = hashlib.sha256(callback_id).hexdigest()

        return callback_id

    def store_approval_request(self, payload, callback_id):

        data = {
            "service_name": self.service_name,
            "callback_id": callback_id,
        }

        for key in payload.keys():
            value = payload[key]
            key = key.replace("--", "").replace("-", "_")

            data[key] = value

        route = "http://dynamodb-helper.jarvis.svc.cluster.local/put_item"
        stored = False

        try:
            response = requests.post(route, json=data)

            if (response.status_code == 200):
                stored = True
            
            else:
                self.send_error_message("couldn't store entry in dynamodb, see service's logs for more information")
        
        except requests.exceptions.ConnectionError:
            logging.info(f" | Couldn't resolve '{route}'")

            self.send_error_message("couldn't store entry in dynamodb, service isn't reachable. Check service's logs for more information")
        

        return stored
    
    def delete_approval_request(self, callback_id):
        data = {
            "callback_id": callback_id
        }

        route = "http://dynamodb-helper.jarvis.svc.cluster.local/delete_item"
        deleted = False

        try:
            response = requests.post(route, json=data)

            if (response.status_code == 200):
                deleted = True
        
        except requests.exceptions.ConnectionError:
            logging.info(f" | Couldn't resolve '{route}'")

            self.send_error_message("Couldn't delete entry in dynamodb, service isn't reachable. Check service's logs for more information")
        

        return deleted

    def send_approval_prompt(self, callback_id, target, users):
        logging.info(f" | {target} requires approval, sending prompt ...")
        
        attachments_text = ""

        for user_id in users:

            attachments_text += f"<@{user_id}> "


        attachments_text += f"\n*Approval required* \n*- Service:* `{self.service_name}` \n*- Target:* `{target}`"
        

        attachments = [
            {
                "text": attachments_text,
                "callback_id": callback_id,
                "color": "#4F93BE",
                "attachment_type": "default",
                "actions": [
                        {
                            "type": "button",
                            "text": "Approved",
                            "name": "approved",
                            "value": "approved",
                            # Green
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": "Not Approved",
                            "name": "not_approved",
                            "value": "not_approved",
                            # Red
                            "style": "danger"
                        }
                    ]
            }
        ]

        self.send_response(attachments)

        return callback_id

    def log_action(self, payload, role_session_name, approver_user_id, callback_id):
        logging.info(f"\n[+] Logging Action ...")


        if (approver_user_id != "None"):
            approver = self.get_username(approver_user_id)
        
        else:
            approver = "None"



        if ("--aws-region" in payload.keys()):
            aws_region = payload["--aws-region"]
        
        else:
            aws_region = "global"
    

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")

        time = now.strftime("%H:%M:%S")

        data = {
            "metadata": {
                "date": date,
                "time": time
            },
            "event": {
                "action": self.service_name,
                "user": self.get_username(self.user_id),
                "aws_account_id": payload["--aws-account-id"],
                "aws_region": aws_region,
                "targets": payload["--targets"],
                "role_session_name": role_session_name
            },
            "approval": {
                "approver": approver,
                "approval_prompt_id": callback_id
            }
        }

        route = "http://s3-helper.jarvis.svc.cluster.local/put_object"

        try:
            response = requests.post(route, json=data)
        
        except requests.exceptions.ConnectionError:
            logging.info(f" | Couldn't resolve '{route}'")

            self.send_error_message("Couldn't log action in S3, service isn't reachable. This action will not be completed. Check service's logs for more information")
