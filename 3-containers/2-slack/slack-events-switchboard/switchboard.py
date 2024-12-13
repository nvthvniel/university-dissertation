import logging, requests, os, ast

class switchboard:

    def __init__(self, __bot_id, __command_mappings, __channel_id, __thread_id, __user_id, __event_type, __event_text):
        self.bot_id = __bot_id
        self.command_mappings = __command_mappings
        self.channel_id = __channel_id
        self.thread_id = __thread_id
        self.user_id = __user_id
        self.event_type = __event_type
        self.event_text = __event_text
    
    def send_response(self, attachments, text = ""):
        payload = {
            "channel": self.channel_id,
            "thread_ts": self.thread_id,
            "text": text,
            "attachments": attachments
        }

        response = requests.post("http://helper.slack.svc.cluster.local", json={"method": "chat.postMessage", "payload": payload})

    def send_error_message(self, message):
        service = os.getenv("K_SERVICE")

        attachments_text = f"*Error*\n*- Service Name:* {service}\n*- Message:* {message}"
            
        attachments = [{"text": attachments_text, "color": "#FF7369"}]
        self.send_response(attachments)

    def output_event_data(self):

        logging.info(f"\n[+] Event Details")
        logging.info(f" | Channel ID: {self.channel_id}")
        logging.info(f" | Thread ID: {self.thread_id}")
        logging.info(f" | User ID: {self.user_id}")
        logging.info(f" | Event Type: {self.event_type}")
        logging.info(f" | Event Text: {self.event_text}")
    
    # Handle no text
    def check_text(self):
        self.event_text = self.event_text.replace(f"<@{self.bot_id}> ", "")

        if (len(self.event_text) > 0):
            self.event_text = self.event_text.split(" ")

        else:
            logging.info("\n[-] No text")
            self.event_text = None

    # Get user's command
    def get_command(self):
        try:
            command = self.event_text[0]
        
        except TypeError:
            logging.info("\n[-] No command given")
            command = None
        
        return command
    
    # Get user's prompt
    def get_prompt(self):
        try:
            prompt = self.event_text[1:]

            if (prompt == []):
                prompt = None
            
            else:
                prompt = ' '.join(prompt)
        
        # No prompt
        except IndexError:
            logging.info("\n[-] No prompt")
            prompt = None
        
        # No text
        except TypeError:
            logging.info("\n[-] No prompt")
            prompt = None
        
        return prompt

    # Use ChatGPT to determine command
    def invoke_chatgpt(self):
        command = None
        prompt = None

        data = {"channel_id": self.channel_id, "thread_id": self.thread_id, "prompt": self.event_text}

        route = "http://chatgpt-helper.jarvis.svc.cluster.local/chat_completion"


        try:

            response = requests.post(route, json=data)
            logging.info(response.text)

            if (response.status_code == 200):
                logging.info(f" | Identified command via ChatGPT")

                response = ast.literal_eval(response.text)

                aws_account_id = response["aws_account_id"]
                aws_region = response["aws_region"]
                command = response["command"]
                targets = response["targets"]

                targets = ','.join(targets)

                prompt = f"--targets {targets} --aws-account-id {aws_account_id} "

                if (aws_region != None):
                    prompt += f"--aws-region {aws_region}"

            else:
                logging.info(f" | Couldn't idenfify command")
                self.send_error_message(f"Couldn't determine command from prompt. Please be more specific or use the usage information provided by the help menu")
        

        # Couldn't reach helper
        except requests.exceptions.ConnectionError:
            logging.info(f" | Couldn't resolve '{route}'")

            self.send_error_message(f"Couldn't reach associated service, '{route}'. Please check the commands mapping and available routes")



        return command, prompt

    # Hanlde event
    def handle_event_type(self):
        if (self.event_type == "app_mention"):
            logging.info(f"\n[+] Handling App Mention Event ...")

            self.check_text()

            user_command = self.get_command()

            user_prompt = self.get_prompt()



            if (self.event_text == None):
                logging.info(f" | No text in event")
                self.send_error_message(f"No text provided")


            elif (user_command == None):
                logging.info(f" | No command in event")
                self.send_error_message(f"Command couldn't be determined, use help for correct syntax")

            
            elif ( user_command not in list(self.command_mappings.keys()) ):
                user_command, user_prompt = self.invoke_chatgpt()
            


            if ( user_command in list(self.command_mappings.keys()) ):

                logging.info(f" | Command: {user_command}")
                logging.info(f" | Prompt: {user_prompt}")

                route = f"{self.command_mappings[user_command]}/event"

                data = {
                    "channel_id": self.channel_id, 
                    "original_user_id": self.user_id, 
                    "thread_id": self.thread_id, 
                    "user_prompt": user_prompt
                }

                try:
                    response = requests.post(route, json=data)
                    logging.info(f" | Sent to {route}")

                
                except requests.exceptions.ConnectionError:
                    logging.info(f" | Couldn't resolve '{route}'")
                    self.send_error_message(f"Couldn't reach associated service, '{route}'. Please check the commands mapping and available routes")
            
            else:
                logging.info(f" | Couldn't handle event")
                self.send_error_message(f"Couldn't handle event, didn't meet defined conditions")

    
        else:
            logging.info(f" | Unrecognised Event Type")
            self.send_error_message(f"Unrecognised event type '{self.event_type}'")

    def main(self):
        self.output_event_data()
        self.handle_event_type()
