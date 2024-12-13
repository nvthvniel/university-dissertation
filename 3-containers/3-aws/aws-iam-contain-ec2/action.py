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

        response_codes = []


        ### EC2 Tags
        client = self.session.client("ec2")
        paginator = client.get_paginator('describe_instances')

        tags = None
        instance_profiles = None
        roles = None

        try:

            response_iterator = paginator.paginate(
                InstanceIds=self.payload["--targets"]
            )

            tags = {}
            instance_profiles = {}

            for page in response_iterator:
                for line in page["Reservations"]:

                    for instance in line["Instances"]:
                        instance_id = instance["InstanceId"]
                        instance_profile = instance["IamInstanceProfile"]["Arn"]

                        try:
                            instance_tags = instance["Tags"]
                        
                        # Instance has no tags
                        except KeyError:
                            instance_tags = None


                        tags[instance_id] = instance_tags
                        instance_profiles[instance_id] = instance_profile
            

            response_codes.append(200)
        
        # Handle errors
        except botocore.exceptions.ClientError as error:

            # User supplied list contains non-existant instance ID
            if error.response['Error']['Code'] == 'InvalidInstanceID.Malformed':
                logging.info(f" | Error: Couldn't find Instance matching specified IDs: {self.payload['--targets']} ...")

                self.service_helper.send_error_message("Couldn't find all instances matching specified IDs")

                
                response_codes.append(500)

            else:
                logging.info(f" | Error: {error}")

                self.service_helper.send_error_message(f"Unhandled response error when trying to get target's tags: {error}")


                response_codes.append(500)




        ### IAM Role Tags
        if (instance_profiles != {}):
            
            roles = {}

            client = self.session.client("iam")

            for target in self.payload["--targets"]:
                instance_profile_name = instance_profiles[target].split("/")[-1]

                response = client.get_instance_profile(InstanceProfileName = instance_profile_name)

                role_name = response["InstanceProfile"]["Roles"][0]["RoleName"]
                roles[target] = role_name

                try:
                    response = client.list_role_tags(RoleName = role_name)

                    role_tags = response["Tags"]

                    if (role_tags == []):
                        role_tags = None

                    else:
                        for role_tag in role_tags:
                            tags[instance_id].append(role_tag)
                    

                    response_codes.append(200)


                except botocore.exceptions.ClientError as error:
                    if error.response['Error']['Code'] == 'NoSuchEntity':
                        logging.info(f" | Error: Couldn't find role matching specified Names: {self.payload['--targets']} ...")

                        self.service_helper.send_error_message("Couldn't find all roles matching specified names")


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
            

        return tags, roles, response_code, response_data

    # Apply block all policy
    def action(self, target):
        logging.info(f"\n[+] Committing Action for {target}...")

        client = self.session.client("iam")

        now = datetime.datetime.now()
        timestamp = now.strftime(f"%Y%m%d%H%M%S")

        policy_name = f"jarvis-disable-role-{target}-{timestamp}"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*"
            }
        }

        policy_document = str(policy_document).replace(" ", "").replace("'", "\"")

        response = client.put_role_policy(
            RoleName = target,
            PolicyName = policy_name,
            PolicyDocument = policy_document
        )

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if (response_code != 200):
            logging.info(f" | Error: Couldn't apply in-line policy: {response}")

            self.service_helper.send_error_message(f"Couldn't disable role")


            response_code = 500
            response_data = {"error": "couldn't apply block-all policy"}
        
        else:
            logging.info(f" | Applied deny all in-line policy")

            attachments_text = f"*Disabled role \"{target}\" with \"{policy_name}\" in-line policy*"
        
            attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
            self.service_helper.send_response(attachments)


            response_code = 200
            response_data = {"success": "applied block-all policy"}
        

        return response_code, response_data

    def pre_approve(self):

        if (self.session != None):
            tags, roles, response_code, response_data = self.get_target_tags()

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
                    response_code, response_data = self.action(roles[target])

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

        
        

