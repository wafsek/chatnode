import http.server
import socketserver
from server.postbox import *
from server.message import Message
from server.person import Person
import json
import uuid
import time
import hashlib

session_IDs = dict()


def make_json_data(rows):
    result = dict()
    for row in rows:
        message = Message(row[0], row[1], row[2], row[3])
        if "messages" in result.keys():
            result["messages"].append(message.__dict__)
        else:
            result["messages"] = [message.__dict__]
    return json.dumps(result, indent=2)


def default_response_data(message):
    result = dict()
    result["Response message"] = message
    return result


def authenticate(session_id):
    if session_id not in session_IDs.keys():
        return False
    else:
        return session_IDs[session_id]


class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        valid = self.is_validate_request()
        if not valid:
            self.respond(400, json.dumps(default_response_data("Bad Request")))
        if self.path == "/fetch":
            email = authenticate(self.headers["UUID"])
            if email:
                self.fetch_messages(email)
            else:
                self.respond(401, json.dumps(default_response_data("Unauthorized")))

    def do_POST(self):
        valid = self.is_validate_request()
        if not valid:
            self.respond(400, json.dumps(default_response_data("Bad Request")))
        if self.path == "/signup":
            self.sign_up()
        elif self.path == "/signin":
            self.sign_in()
        elif self.path == "/signout":
            self.sign_out()
        elif self.path == "/send":
            is_authenticated = authenticate(self.headers["UUID"])
            if is_authenticated:
                self.store_data(is_authenticated)
            else:
                self.respond(401, json.dumps(default_response_data("Unauthorized")))

    def is_validate_request(self):
        if "Content-Type" not in self.headers:
            return False
        if self.path == "/fetch":
            return "UUID" in self.headers
        if self.path == "/signin":
            return self.headers["Content-Type"] == "application/json"
        if self.path == "/signout":
            return "UUID" in self.headers
        if self.path == "/signup":
            return self.headers["Content-Type"] == "application/json"
        if self.path == "/send":
            if "UUID" not in self.headers:
                return False
            return self.headers["Content-Type"] == "application/json"
        return False

    def sign_up(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        json_data = json.loads(data.decode("utf-8"))
        hashed_password = hashlib.sha224(json_data["Password"].encode()).hexdigest()
        person = Person(json_data["Email"], hashed_password)
        self.respond(200, json.dumps(default_response_data(insert_person(person))))

    def sign_in(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        login_data = json.loads(data.decode('utf-8'))
        login_email = login_data["email"]
        hashed_password = hashlib.sha224(login_data["password"].encode()).hexdigest()
        sql_check = check_password(login_email, hashed_password)
        if sql_check:
            session_id = uuid.uuid4().__str__()
            if login_email in session_IDs.values():
                for key, value in dict(session_IDs).items():
                    if value == login_email:
                        del session_IDs[key]
            session_IDs[session_id] = login_email
            response_data = default_response_data("signed in!")
            response_data["UUID"] = session_id
            sign_in_data = json.dumps(response_data, indent=2)
            self.respond(200, sign_in_data,
                         {'Content-Type': 'application/json',
                          'Content-Length': len(sign_in_data).__str__()})
        else:
            self.respond(401, json.dumps(default_response_data("Sign in failed"), indent=2))

    def sign_out(self):
        if self.headers["UUID"] in session_IDs:
            del session_IDs[self.headers["UUID"]]
            self.respond(200, json.dumps(default_response_data("Signed out")))

        else:
            self.respond(401, json.dumps(default_response_data("Not authenticated")))

    def store_data(self, authentication):
        data = self.rfile.read(int(self.headers['Content-Length']))
        message = json.loads(data.decode("utf-8"))
        message["from_email"] = authentication
        message["time"] = int(time.time())
        insert_message(message)
        self.respond(200, json.dumps(default_response_data('Message sent')))

    def fetch_messages(self, email):
        messages = make_json_data(fetch_messages_to_email(email))
        self.respond(200, messages, {'Content-Type': 'application/json'})

    def is_authorised(self):
        self.respond(401, json.dumps(default_response_data('Not authorized')))

    def respond(self, code=200, response_message=None, headers=None):
        data_load = response_message.encode()
        self.send_response(code)
        if headers:
            for header in headers:
                self.send_header(header, headers[header])
        self.end_headers()
        if response_message:
            self.wfile.write(data_load)


class ChatNode:
    """A ChatNode class"""
    def __init__(self, handler, address="localhost", port=8000):
        self.__port = port
        self.__address = address
        self.__handler = handler
        self.httpd = socketserver.TCPServer((self.__address, self.__port),
                                            self.__handler)

    def serve(self):
        print("serving at port", self.__port)
        self.httpd.serve_forever()


ChatNode(MyHandler, "0.0.0.0", 8000).serve()
