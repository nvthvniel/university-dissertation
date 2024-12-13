import boto3, botocore, logging, json, datetime
from service_helper import service_helper

class action:

    # Constructor
    def __init__ (self, __require_approval, __approvers, __arguments, __channel_id, __user_id, __thread_id, __user_prompt):
        self.require_approval = __require_approval
        self.approvers = __approvers
        self.arguments = __arguments
        self.channel_id = __channel_id
        self.user_id = __user_id
        self.thread_id = __thread_id
        self.user_prompt = __user_prompt

        self.service_helper = service_helper(self.require_approval, self.approvers, self.channel_id, self.user_id, self.thread_id, self.arguments)

        # Format user's input
        self.payload = self.service_helper.extract_payload(self.user_prompt, self.arguments)

        if ( None not in self.payload.values() ):

            if ("--aws-region" in self.payload.keys()):
                aws_region = self.payload["--aws-region"]
            
            else:
                aws_region = "us-east-1"

            self.email = self.service_helper.get_username(self.user_id)
            self.session = self.service_helper.create_session(aws_region, self.payload["--aws-account-id"], self.email)
            self.users = self.service_helper.get_userid()

    # Get tags
    def get_target_tags(self):
        logging.info("\n[+] Getting Targets' Tags ...")

        tags = {}
        response_codes = []

        client = self.session.client("iam")

        for target in self.payload["--targets"]:

            try:
                response = client.list_user_tags(UserName = target)

                user_tags = response["Tags"]

                if (user_tags == []):
                    user_tags = None

                tags[target] = user_tags

                response_codes.append(200)

            except botocore.exceptions.ClientError as error:
                if error.response['Error']['Code'] == 'NoSuchEntity':
                    logging.info(f" | Error: Couldn't find users matching specified Names: {self.data['targets']} ...")

                    self.service_helper.send_error_message("Couldn't find all users matching specified names")


                    response_codes.append(500)

                else:
                    logging.info(f" | Error: {error}")

                    self.service_helper.send_error_message(f"Unhandled response error when trying to get target's tags: {error}")


                    response_codes.append(500)
        


        if (500 in response_codes):
            response_code = 500
            response_data = {"error": "couldn't find all targets"}
        
        else:
            response_code = 200
            response_data = {"success": "retrieved all tags"}
        

        return tags, response_code, response_data

    # Disable IAM user
    def action(self, target):
        logging.info(f"\n[+] Committing Action for {target}...")

        client = self.session.client("iam")

        now = datetime.datetime.now()
        timestamp = now.strftime(f"%Y%m%d%H%M%S")

        policy_name = f"jarvis-disable-user-{target}-{timestamp}"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*"
            }
        }

        policy_document = str(policy_document).replace(" ", "").replace("'", "\"")

        response = client.put_user_policy(
            UserName = target,
            PolicyName = policy_name,
            PolicyDocument = policy_document
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if (response_code != 200):
            logging.info(f" | Error: Couldn't apply in-line policy: {response}")

            self.service_helper.send_error_message(f"Couldn't disable user")


            response_code = 500
            response_data = {"erorr": "couldn't apply block-all policy"}
        
        else:
            logging.info(f" | Applied deny all in-line policy")

            attachments_text = f"*Disabled user \"{target}\" with \"{policy_name}\" in-line policy*"
        
            attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
            self.service_helper.send_response(attachments)


            response_code = 200
            response_data = {"success": "applied block-all policy"}
        

        return response_code, response_data

    def pre_approve(self):

        if (self.session != None):
            tags, response_code, response_data = self.get_target_tags()

            approval_requirements = self.service_helper.check_approval_scope(tags)

            for target in approval_requirements.keys():

                if (approval_requirements[target] == True):
                    callback_id = self.service_helper.generate_callback_id(target)

                    stored = self.service_helper.store_approval_request(self.payload, callback_id)

                    if (stored == True):
                        self.service_helper.send_approval_prompt(callback_id, target, self.users)
                        response_code = 401
                        response_data = {"success": "stored approval prompt"}
                    
                    else:
                        response_code = 500
                        response_data = {"error": "failed to store approval prompt"}
                        break
                    
                else:
                    response_code, response_data = self.action(target)

                    if (response_code == 200):
                        self.service_helper.log_action(self.payload, f"jarvis-incident-response-{self.email}", "None", "None")   

                    else:
                        break

        else:
            response_code = 500
            response_data = {"error": "couldn't authenticate to aws"} 
        
        return response_code, response_data

    def post_approve(self, callback_id, response_value, approver_user_id):
        
        if (self.session != None):

            valid = self.service_helper.validate_approver_response(response_value, callback_id, approver_user_id, self.users)
            
            if (valid == True):
                logging.info(f"\n[+] Approval valid")

                for target in self.payload["--targets"]:
                    response_code, response_data = self.action(target)

                    if (response_code == 200):
                        self.service_helper.log_action(self.payload, f"jarvis-incident-response-{self.email}", "None", "None")   

                    else:
                        break
                    
                    
            
            else:
                logging.info(f"\n[+] Approval not valid")

                response_code = 500
                response_data = {"error": "invalid approval"}
        
        else:
            response_code = 500
            response_data = {"error": "couldn't authenticate to aws"}
        
        return response_code, response_data