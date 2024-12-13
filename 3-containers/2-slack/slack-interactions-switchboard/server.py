from http.server import BaseHTTPRequestHandler, HTTPServer
from read_configmap import read_configmap
from urllib.parse import unquote
from switchboard import switchboard
import logging, requests, json, hashlib, hmac, datetime, time, os

class http_server:

    def __init__(self, __server_name, __server_port):
        self.server_name = __server_name
        self.server_port = __server_port

        server = HTTPServer( (self.server_name, self.server_port), handler)

        logging.info(f"\n[+] Server Started: {self.server_name}:{self.server_port}")

        server.configs = self.read_configmap()
        server.buffer = {}
        
        server.serve_forever()
    
    def read_configmap(self):
        config_path = "/home/autouser/scripts/config"
        file_names = ["bot_id", "commands.mapping"]

        obj = read_configmap(config_path, file_names)
        configs = obj.main()

        return configs


class handler(BaseHTTPRequestHandler):

    # Disable HTTPServer log message output
    def log_message(self, format, *args):
        return

    def do_GET(self):
        self.send_response(404)
        self.end_headers()
    
    def calc_event_id(self, channel_id, event_ts):
        event_id = f"{channel_id}{event_ts}"
        event_id = event_id.encode("utf-8")
        event_id = hashlib.sha256(event_id).hexdigest()

        return event_id
    
    def auth_event(self, slack_timestamp, slack_signature, body):
        logging.info(f"\n[+] Authenticating Event ...")
        authed = False

        local_timestamp = int(time.time())

        logging.info(f" | Slack timestamp: {slack_timestamp}")
        logging.info(f" | Local timestamp: {local_timestamp}")

        # Event is > 5 minutes old
        if ( (local_timestamp - slack_timestamp) > 60 * 5 ):
            logging.info(f" | Possible replay attack, skipping event ...")
        
        else:
            signing_secret = os.getenv("SLACK_SIGNING_SECRET")

            logging.info(f" | Slack Signing Secret: {signing_secret[0:5]}...")

            signing_secret = bytes(signing_secret, "utf-8")

            version_number = "v0"
            sig_basestring = f"{version_number}:{slack_timestamp}:{body}"
            #logging.info(f" | Basestring: {sig_basestring}")

            sig_basestring = bytes(sig_basestring, "utf-8")

            basestring_hash = hmac.new(
                signing_secret,
                sig_basestring,
                hashlib.sha256
            ).hexdigest()

            logging.info(f" | Slack signature: {slack_signature}")

            local_signature = f"v0={basestring_hash}"
            logging.info(f" | Local signature: {local_signature}")

            if ( hmac.compare_digest(local_signature, slack_signature) ):
                authed = True
                logging.info(f" | Signatures match, authentic")
            
            else:
                logging.info(f" | Signatures differ, not authentic")
            
        return authed

    def do_POST(self):

        path = str(self.path)

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        body_raw = post_data.decode('utf-8')

        event_id = None
        retry = False
        authed = False

        if (len(body_raw) != 0):
            try:

                if ("X-Slack-Retry-Num" in self.headers.keys()):
                    retry = True
                
                else:
                    now = datetime.datetime.now()
                    now = now.strftime("%Y-%m-%d %H:%M:%S")
                    
                    logging.info(f"\n--- {now} | Received POST request ---")
                    
                    authed = self.auth_event(int(self.headers["X-Slack-Request-Timestamp"]), self.headers["X-Slack-Signature"], body_raw)


                if (authed == True):
                    body = unquote(body_raw)
                    body = body.strip("payload=")
                    body = json.loads(body)

                    event_id = self.calc_event_id(body["channel"]["id"], body["trigger_id"])
            
            except json.decoder.JSONDecodeError:
                logging.info(f" | Error decoding JSON: {body}")
        
        else:
            body = None

        
        # Not repeat and authentic
        if ( (event_id != None) and (retry == False) and (authed == True) ):

             # Ignore repeat
            if ( (body["type"] in self.server.buffer.keys()) and (self.server.buffer[body["type"]] == event_id) ):
                logging.info(f" | Ignoring duplicate message")

                # Send response
                self.send_response(429)
                self.end_headers()

            # elif (body["callback_id"] in self.server.history):
            #     logging.info(f" | Detected re-click, sending error message")


            #     attachments_text = "*Error:* response has already been provided"
            #     attachments = [{"text": attachments_text, "color": "#FF7369"}]
                
            #     payload = {
            #         "channel": body["channel"]["id"],
            #         "thread_ts": body["original_message"]["thread_ts"],
            #         "text": "",
            #         "attachments": attachments
            #     }

            #     response = requests.post("http://helper.slack.svc.cluster.local", json={"method": "chat.postMessage", "payload": payload})
            #     logging.info(f" | Response: {response}")

            channel_id = body["channel"]["id"]
            thread_id = body["original_message"]["thread_ts"]
            original_user_id = body["original_message"]["parent_user_id"]
            approver_user_id = body["user"]["id"]
            event_type = body["type"]
            callback_id = body["callback_id"]
            response = body["actions"][0]["name"]

            switchboard_obj = switchboard(self.server.configs["commands.mapping"], channel_id, thread_id, original_user_id, approver_user_id, event_type, callback_id, response)
            switchboard_obj.main()

            self.send_response(200)
            self.end_headers()

            self.server.buffer[event_type] = event_id

if __name__ == '__main__':

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    server_name = "localhost"
    server_port = 5555

    http_server(server_name, server_port)