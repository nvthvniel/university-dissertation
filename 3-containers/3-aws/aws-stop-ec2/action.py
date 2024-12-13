import boto3, botocore, logging, json
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

        client = self.session.client("ec2")
        paginator = client.get_paginator('describe_instances')

        tags = None

        try:

            response_iterator = paginator.paginate(
                InstanceIds=self.payload["--targets"]
            )

            tags = {}

            for page in response_iterator:
                for line in page["Reservations"]:

                    for instance in line["Instances"]:
                        instance_id = instance["InstanceId"]

                        try:
                            instance_tags = instance["Tags"]
                        
                        # Instance has no tags
                        except KeyError:
                            instance_tags = None


                        tags[instance_id] = instance_tags
            

            response_code = 200
            response_data = {"success": "retrieved all tags"}
        
        # Handle errors
        except botocore.exceptions.ClientError as error:

            # User supplied list contains non-existant instance ID
            if error.response['Error']['Code'] == 'InvalidInstanceID.Malformed':
                logging.info(f" | Error: Couldn't find Instance matching specified IDs: {self.payload['--targets']} ...")

                self.service_helper.send_error_message("Couldn't find all instances matching specified IDs")


                response_code = 500
                response_data = {"error": "couldn't find all targets"}

            else:
                logging.info(f" | Error: {error}")

                self.service_helper.send_error_message(f"Unhandled response error when trying to get target's tags: {error}")


                response_code = 500
                response_data = {"error": "unhandled error"}
        

        return tags, response_code, response_data

    # Stop instances
    def action(self, target):
        logging.info(f"\n[+] Committing Action for {target}...")

        client = self.session.client("ec2")

        response = client.stop_instances(InstanceIds=[target])

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]

        if (response_code != 200):
            logging.info(f" | Error: Couldn't stop Instance '{target}'")

            self.service_helper.send_error_message(f"Couldn't stop EC2 instance '{target}': {response}")

            response_code = 500
            response_data = {"error": f"Couldn't stop EC2 instance '{target}': {response}"}
        
        else:
            logging.info(f" | Stopped Instance '{target}'")

            attachments_text = f"*'{target}' has been stopped*"
            
            attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
            self.service_helper.send_response(attachments)

            response_code = 200
            response_data = {"success": "completed action"}
        
        
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