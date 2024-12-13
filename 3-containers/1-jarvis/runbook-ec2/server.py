from http.server import BaseHTTPRequestHandler, HTTPServer
from read_configmap import read_configmap
from runbook import runbook
import logging, json, datetime

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
        file_names = ["services"]

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
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
                    
        logging.info(f"\n--- {now} | Received POST request ---")


        # Filter input data
        path = str(self.path)
        headers = str(self.headers).replace("\n", "")

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
        logging.info(f" | Headers: {headers}")
        logging.info(f" | Body: {body}")


        logging.info(f"\n[+] Configuration Values")
        for key in self.server.configs.keys():
            logging.info(f" | {key}: {self.server.configs[key]}")
        
        response_data = None
        response_code = 500

        if (path == "/event"):

            obj = runbook(self.server.configs["services"], body)
            response_code = obj.main()
        

        else:
            logging.info(f"[!] Error: unrecognised path: {path}")
        

        logging.info(f"\n[+] Sending response ...")
        logging.info(f" | Status Code: {response_code}")
        logging.info(f" | Response Data: {response_data}")


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