from http.server import BaseHTTPRequestHandler, HTTPServer
from helper import helper
import logging, json, os, datetime

class http_server:

    def __init__(self, __server_name, __server_port):
        self.server_name = __server_name
        self.server_port = __server_port

        server = HTTPServer( (self.server_name, self.server_port), handler)

        logging.info(f"\n[+] Server Started: {self.server_name}:{self.server_port}")

        server.serve_forever()

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

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        body = post_data.decode('utf-8')

        try:
            body = json.loads(body)
        
        except json.decoder.JSONDecodeError:
            logging.info(f" | Error decoding JSON: {body}")
            body = None
        

        # Output Data
        logging.info(f"\n[+] Request Data")
        logging.info(f" | Body: {body}")

        if ( (body != None) and (type(body) == dict) ):

            payload = [
                ("token", os.getenv("SLACK_API_TOKEN")),
            ]

            for key in body["payload"].keys():
                payload.insert( len(payload), (key, body["payload"][key]) )


            method = body["method"]
            payload = payload

            logging.info("\n[+] Calling Slack API ...")

            response = helper.api_call(method, payload)

            logging.info(f" | Response: {response}")

            # Send response
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write( bytes(response, "utf8") )
        
        else:
            logging.info(" | Error")

            # Send response
            self.send_response(400)
            self.end_headers()

if __name__ == '__main__':

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    server_name = "localhost"
    server_port = 5555

    http_server(server_name, server_port)