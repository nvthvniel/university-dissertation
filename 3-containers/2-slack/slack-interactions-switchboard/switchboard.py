import logging, requests, ast, os

class switchboard:

    def __init__(self, __commands_mapping, __channel_id, __thread_id, __original_user_id, __approver_user_id, __event_type, __callback_id, __response):
        self.command_mappings = __commands_mapping
        self.channel_id = __channel_id
        self.thread_id = __thread_id
        self.original_user_id = __original_user_id
        self.approver_user_id = __approver_user_id
        self.event_type = __event_type
        self.callback_id = __callback_id
        self.response = __response
    
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
        logging.info(f" | Original User ID: {self.original_user_id}")
        logging.info(f" | Approver User ID: {self.approver_user_id}")
        logging.info(f" | Event Type: {self.event_type}")
        logging.info(f" | Callback ID: {self.callback_id}")
        logging.info(f" | Response: {self.response}")

    def get_item(self):
        data = {
            "callback_id": self.callback_id
        }

        route = "http://dynamodb-helper.jarvis.svc.cluster.local/get_item"
        
        retrieved_status = False
        retrieved_data = None

        try:
            response = requests.post(route, json=data)

            if (response.status_code == 200):
                retrieved_status = True

                retrieved_data = ast.literal_eval(response.text)
            
            elif (response.status_code == 500):
                logging.info(f" | Error: user re-clicked a button")
            
            else:
                logging.info(f" | Error: {response.status_code}")


        
        except requests.exceptions.ConnectionError:
            logging.info(f" | Couldn't resolve '{route}'")

            self.send_error_message("Couldn't get entry in dynamodb, service isn't reachable. Check service's logs for more information")
        

        return retrieved_status, retrieved_data

    def validate_approver(self):

        valid = False

        if (self.original_user_id != self.approver_user_id):
            valid = True
        
        return valid

    def validate_service(self, service_name):
        valid = False

        if ( service_name in list(self.command_mappings.keys()) ):
            valid = True
            
        return valid

    def handle_event_type(self):
        if (self.event_type == "interactive_message"):
            logging.info(f"\n[+] Handling Button Press Event ...")

            
            retrieved_status, retrieved_data = self.get_item()
            logging.info(f" | Retrieved Status: {retrieved_status}")
            logging.info(f" | Retrieved Data: {retrieved_data}")


            # Couldn't retrieve entry from dynamodb. Likely a repress of button
            if (retrieved_status == False):
                logging.info(f" | Error: invalid retrieval from dynamodb, sending error message")

                self.send_error_message(f"a response for this action has already been receieved")

            
            # Retrieved data from dynamodb
            else:
                service_name = retrieved_data["service_name"]


                valid_approval = self.validate_approver()
                valid_service = self.validate_service(service_name)


                # Service exists, can be forwarded for actioning
                if ( (retrieved_status == True) and ( valid_approval == True ) and (valid_service == True) ):
                    route = f"{self.command_mappings[service_name]}/interaction"

                    # targets = str(retrieved_data["targets"])
                    # targets = targets.strip("[").strip("]").replace("'", "").replace(", ", ",")

                    data = {
                        "channel_id": self.channel_id, 
                        "original_user_id": self.original_user_id,
                        "approver_user_id": self.approver_user_id,
                        "thread_id": self.thread_id,
                        "response_value": self.response,
                        "callback_id": retrieved_data["callback_id"]
                    }

                    user_prompt = ""

                    for key in retrieved_data.keys():

                        if ( (key != "service_name") and (key not in data.keys()) ):
                            item = key.replace("_", "-")
                            item = f"--{item}"
                            
                            value = retrieved_data[key]
                            value = value.replace("[", "").replace("]", "").strip("'")
                        

                            user_prompt += f"{item} {value} "

                    data["user_prompt"] = user_prompt

                    try:
                        response = requests.post(route, json=data)
                        logging.info(f" | Sent to {route}")

                    
                    except requests.exceptions.ConnectionError:
                        logging.info(f" | Couldn't resolve '{route}'")

                        self.send_error_message(f"Couldn't reach associated service, '{route}'. Please check the commands mapping and available routes")

                elif (valid_approval == False):
                    logging.info(f" | Error: invalid approver, sending error message")

                    self.send_error_message(f"<@{self.approver_user_id.upper()}> can't approve their own response action")
                
                elif (valid_service == False):
                    logging.info(f" | Error: invalid service, sending error message")

                    self.send_error_message(f"couldn't find route for service '{service_name}'")

    
        else:
            logging.info(f" | Unrecognised Event Type")

            self.send_error_message(f"Unrecognised event type, '{self.event_type}'")

                
    def main(self):
        self.output_event_data()
        self.handle_event_type()


