import requests, logging, os, ast

class help:

    def __init__(self, __channel_id, __thread_id, __command_mappings):
        self.channel_id = __channel_id
        self.thread_id = __thread_id
        self.command_mappings = __command_mappings

    def send_response(self, attachments, blocks = "", text = ""):

        payload = {
            "channel": self.channel_id,
            "thread_ts": self.thread_id,
            "text": text,
            "blocks": str(blocks),
            "attachments": attachments
        }

        response = requests.post("http://helper.slack.svc.cluster.local", json={"method": "chat.postMessage", "payload": payload})
        response = ast.literal_eval(response.text)

        if (response["ok"] != True):
            logging.info(f" | Error: {response}")

    def send_error_message(self, message):
        service = os.getenv("K_SERVICE")

        message = message.capitalize()

        attachments_text = f"*Error*\n*- Service Name:* {service}\n*- Message:* {message}"
            
        attachments = [{"text": attachments_text, "color": "#FF7369"}]
        self.send_response(attachments)
    
    def create_manual(self):
        if  (self.command_mappings == {}):
            logging.info(f"\n[-] Sending Error Message, No Commands Mapping")

            self.send_error_message("no commands mappings set")


        else:
            logging.info(f"\n[+] Sending Help Menu")


            # We're using blocks rather than attachments as the help menu has more detailed information. 
            # Laying this out in a decent way isn't really possible using attachments
        
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "List of all supported commands"
                    }
                },
                {
                    "type": "divider"
                }
            ]


            for command in self.command_mappings.keys():
                description = self.command_mappings[command]["description"]
                usage = self.command_mappings[command]["usage"]

                # Header for command
                blocks.append(
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{command}"
                        }
                    }
                )

                # Description + Usage information
                blocks.append(
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Description:* {description}\n"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Usage:* `{usage}`\n"
                            }
                        ]
                    }
                )

            
            self.send_response(attachments="", blocks=blocks, text="")
    
    def main(self):
        self.create_manual()