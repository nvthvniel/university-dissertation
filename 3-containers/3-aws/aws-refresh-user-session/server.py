from http.server import BaseHTTPRequestHandler, HTTPServer
from read_configmap import read_configmap
from action import action
import logging, json

class http_server:

    def __init__(self, __server_name, __server_port):
        self.server_name = __server_name
        self.server_port = __server_port

        server = HTTPServer( (self.server_name, self.server_port), handler)

        logging.info(f"\n[+] Server Started: {self.server_name}:{self.server_port}")

        server.configs = self.read_configmap()
        server.serve_forever()
    
    def read_configmap(self):
        config_path = "/home/autouser/scripts/config"
        file_names = ["require_approval", "approvers", "arguments"]

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

    def do_POST(self):
        logging.info(f"\n--- Received POST request ---")

        response_code = 500
        response_data = {"error": "default server error"}


        # Filter input data
        path = str(self.path)

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        body = post_data.decode('utf-8')

        try:
            body = json.loads(body)
        
        except json.decoder.JSONDecodeError:
            logging.info(f" | Error decoding JSON: {body}")
            body = None
        

        # Output Data
        logging.info(f"\n[+] Request Data")
        logging.info(f" | Path: {path}")
        logging.info(f" | Body: {body}")


        logging.info(f"\n[+] Configuration Values")
        for key in self.server.configs.keys():
            logging.info(f" | {key}: {self.server.configs[key]}")
        

        obj = action(
            self.server.configs["require_approval"], 
            self.server.configs["approvers"], 
            self.server.configs["arguments"], 
            body["channel_id"], 
            body["original_user_id"],
            body["thread_id"],
            body["user_prompt"]
        )

        if (path == "/event"):
            response_code, response_data = obj.pre_approve()
        
        elif (path == "/interaction"):
            response_code, response_data = obj.post_approve(body["callback_id"], body["response_value"], body["approver_user_id"])

        # Send response
        self.send_response(response_code)
        self.end_headers()

        if (response_data != None):
            self.wfile.write(bytes(str(response_data), "utf-8"))
            self.wfile

if __name__ == '__main__':

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    server_name = "localhost"
    server_port = 5555

    http_server(server_name, server_port)