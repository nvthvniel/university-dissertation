import logging, requests, json

class runbook:

    def __init__ (self, __services, __data):
        self.services = __services
        self.data = __data
    
    def send_response(self, attachments, text = ""):
        logging.info("\n[+] Sending Slack Response ...")

        payload = {
            "channel": self.data["channel_id"],
            "thread_ts": self.data["thread_id"],
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
    
    def iterate(self):
        logging.info(f"\n[+] Calling Runbook's Services ...")

        response_codes = []

        data = {
            "channel_id": self.data["channel_id"], 
            "original_user_id": self.data["original_user_id"], 
            "thread_id": self.data["thread_id"], 
            "user_prompt": self.data["user_prompt"]
        }

        for service in self.services:
            try:
                response = requests.post(f"{service}/event", json=data)

                # Completed successfully
                if (response.status_code == 200):
                    response_codes.append(200)

                    logging.info(f" | {service}: success")
                
                # Requires approval
                elif (response.status_code == 401):
                    response_codes.append(401)

                    logging.info(f" | {service}: requires approval")

                
                # Error
                else:
                    response_codes.append(500)

                    logging.info(f" | {service}: errored, {response.text}")

                    break

            
            except requests.exceptions.ConnectionError:
                logging.info(f" | Couldn't resolve '{service}'")
                self.send_error_message(f"Couldn't reach associated service, '{service}'. Please check the commands mapping and available routes")
        


        response_codes.sort()

        # Service failed
        if (500 in response_codes):
            response_code = 500

            self.send_error_message(f"An action failed and the runbook has been stopped. Please review the service's logs for more information")
        
        # All successful
        elif ( ( set(response_codes) == {200} ) or ( set(response_codes) == {200, 401} ) ):
            response_code = 200

            attachments_text = f"*Completed runbook*"
        
            attachments = [{"text": attachments_text, "color": "#4DAB9A"}]
            self.send_response(attachments)
        

        return response_code
    
    def main(self):
        response_code = self.iterate()

        return response_code