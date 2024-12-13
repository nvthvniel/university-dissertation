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

    def action(self, target):
        logging.info(f"\n[+] Committing Action for {target}...")

        now = datetime.datetime.now()
        timestamp = now.strftime(f"%Y%m%d%H%M%S")

        vpc_id = None
        security_group_id = None
        security_group_name = f"jarvis-network-contain-{target}-{timestamp}"

        client = self.session.client("ec2")



        # 1. get vpc
        response = client.describe_instances(InstanceIds = [target])

        response_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if (response_code != 200):
            logging.info(f" | Error: Couldn't get VPC ID")

            self.service_helper.send_error_message(f"Couldn't get '{target}'s VPC ID: {response}")

            
            response_code = 500
            response_data = {"error": "couldn't get vpc id"}
        
        else:
            vpc_id = response["Reservations"][0]["Instances"][0]["VpcId"]

            logging.info(f" | VPC ID: {vpc_id}")
        
        

        # 2. create security group
        if (vpc_id != None):

            response = client.create_security_group(
                Description = f"Jarvis Automation by {self.email} - Network Contain EC2 instance",
                GroupName = security_group_name,
                VpcId = vpc_id
            )

            response_code = response["ResponseMetadata"]["HTTPStatusCode"]
            if (response_code != 200):
                logging.info(f" | Error: Couldn't create security group: {response}")

                self.service_helper.send_error_message(f"Couldn't create security group")

                
                response_code = 500
                response_data = {"error": "couldn't create security group"}
            
            else:
                security_group_id = response["GroupId"]

                logging.info(f" | Created security group: {security_group_name} ({security_group_id})")
            

        # 3. Associate security group with ec2 instance
        if ( (vpc_id != None) and (security_group_id != None) ):

            # Remove default egress allow all 
            response = client.revoke_security_group_egress(
                GroupId = security_group_id,
                IpPermissions = [
                    {
                        "IpProtocol": "-1",
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}] 
                    }
                ]
            )

            response_code = response["ResponseMetadata"]["HTTPStatusCode"]
            if (response_code != 200):
                logging.info(f" | Error: Couldn't remove default egress rule from security group: {response}")

                self.service_helper.send_error_message(f"Couldn't remove default egress rule from security group")


                response_code = 500
                response_data = {"error": "couldn't remove default egress rule from security group"}

            
            else:
                logging.info(f" | Removed default egress rule from security group")




            # Associate security group with instance
            response = client.modify_instance_attribute(
                InstanceId = target,
                Groups = [security_group_id]
            )

            response_code = response["ResponseMetadata"]["HTTPStatusCode"]
            if (response_code != 200):
                logging.info(f" | Error: Couldn't assign containment security group: {response}")

                self.service_helper.send_error_message(f"Couldn't assign containment security group")


                response_code = 500
                response_data = {"error": "couldn't assign containment security group"}
            
            else:
                logging.info(f" | Assigned containment security group")

                attachments_text = f"*'{target}' has been network contained with \"{security_group_name}\"*"
            
                attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
                self.service_helper.send_response(attachments)


                response_code = 200
                response_data = {"success": "assigned containment security group"}
        
        
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

        
        

