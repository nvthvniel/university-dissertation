import logging, json, re, boto3, openai, requests, os, ast

class helper:

    def __init__ (self, __channel_id, __thread_id, __user_prompt, __tuning_data, __commands_mapping):
        self.channel_id = __channel_id
        self.thread_id = __thread_id
        self.user_prompt = __user_prompt
        self.tuning_data = __tuning_data
        self.commands_mapping = __commands_mapping

        self.user_prompt = ' '.join(self.user_prompt)
        self.service_name = os.getenv("K_SERVICE")
    
    def send_response(self, attachments, text = ""):
        logging.info("\n[+] Sending Slack Response ...")

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
    
    # Authenticate to AWS
    def create_aws_client(self):
        logging.info(f"\n[+] Authenticating To AWS ...")

        client = boto3.client("ec2")

        return client
    
    # Authenticate to ChatGPT
    def create_chatgpt_client(self):
        logging.info(f"\n[+] Authenticating To ChatGPT ...")

        client = openai.OpenAI(api_key = os.getenv("CHATGPT_API_TOKEN"))

        return client

    def describe_regions(self, aws_client):
        logging.info(f"\n[+] Listing All AWS Regions ...")
        
        regions = []

        response = aws_client.describe_regions(AllRegions=True)

        for item in response["Regions"]:
            regions.append(item["RegionName"])
        
        return regions

    def validate(self, regions):
        logging.info(f"\n[+] Validating User's Prompt ...")

        aws_account_id = None
        aws_region = None
        valid = False


        for region in regions:
            if (region in self.user_prompt):
                aws_region = region
                logging.info(f" | AWS Region: {aws_region}")
        

        search = re.search("\d{12}", self.user_prompt)

        if (search != None):
            aws_account_id = search.group()

            logging.info(f" | AWS Account ID: {aws_account_id}")
        

        if (aws_account_id == None):
            logging.info(f" | Couldn't identify AWS account ID in prompt, sending error ...")

            self.send_error_message("Couldn't identify AWS account ID in prompt")

        else:
            logging.info(f" | Prompt is valid")

            valid = True


        return valid, aws_account_id, aws_region
             

    def chat_completion(self, client):
        logging.info(f"\n[+] Sending Prompt To ChatGPT ...")
        
        # Set instructions for LLM
        system_prompt = "You are going to be used to extract specific pieces of information from prompts written in natural English language that aim to complete security incident response actions within an AWS account. It is your job to determine the targets of the action and what action the user wants to take from the following list. Descriptions of each action will be supplied to help improve your understanding of what they do. If you can't determine the action from the prompt, or an action is not directly tailored to the prompt, please respond with “Action: unsupported”. If you can't determine the targets of the action, please respond with “Targets: unknown”. For the targets you identify, please respond with them in a list, for example “Targets: ”target 1”, “target 2”, …”. Do not include the target's resource type in your response, only its name. Do not respond with the target AWS account ID."


        # Add commands and their description to help tune
        system_prompt += "Here is the list of supported actions with their description."
        for command in self.commands_mapping.keys():
                description = self.commands_mapping[command]["description"]
                system_prompt += f"\n- {command}: {description}"
        

        # Add prompts with correct responses to help tune
        system_prompt += "\nHere is a list of example prompts and their correct responses that you should base your answers on."
        for command in self.tuning_data.keys():
            prompt = self.tuning_data[command]["prompt"]
            response = self.tuning_data[command]["response"]

            system_prompt += f"\n- Prompt: {prompt} \n- Response: {response}"



        
        # logging.info(f" | System Prompt: \n{system_prompt}")
        # logging.info(f" | User Prompt: {self.user_prompt}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.user_prompt}
            ]
        )

        response = response.choices[0].message.content
        response = ast.literal_eval(response)
        logging.info(f" | Response: {response}")

        command = response["Action"]
        targets = response["Targets"]

        logging.info(f" | Command: {command}")
        logging.info(f" | Targets: {targets}")

        return command, targets

    def main(self):
        aws_client = self.create_aws_client()
        regions = self.describe_regions(aws_client)
        valid, aws_account_id, aws_region = self.validate(regions)

        response_code = 500
        response_data = {"aws_account_id": None, "aws_region": None, "command": None, "targets": None}

        if (valid == True):
            chatgpt_client = self.create_chatgpt_client()
            command, targets = self.chat_completion(chatgpt_client)

            response_code = 200
            response_data["aws_account_id"] = aws_account_id
            response_data["aws_region"] = aws_region
            response_data["command"] = command
            response_data["targets"] = targets

        return response_code, response_data