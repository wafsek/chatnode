import http.server
import socketserver
import postbox
from message import Message
from people import Person
import json
import uuid

session_IDs = dict()


def make_json_data(rows):
    result = dict()
    for row in rows:
        message = Message(row[0], row[1], row[2], row[3])
        if "messages" in result.keys():
            result["messages"].append(message.__dict__)
        else:
            result["messages"] = [message.__dict__]
    return json.dumps(result, indent=2).encode()


class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        valid = self.is_validate_request()
        if not valid:
            self.respond(400)
        if self.path == "/fetch":
            email = self.authenticate(self.headers["UUID"])
            if email:
                self.fetch_messages(email)
            else:
                self.respond(401, b"Unauthorized")

    def do_POST(self):
        valid= self.is_validate_request()
        if not valid:
            self.respond(400)
        if self.path == "/signup":
            self.sign_up()
        elif self.path == "/signin":
            self.sign_in()
        elif self.path == "/signout":
            self.sign_out()
        elif self.path == "/send":
            is_authenticated = self.authenticate(self.headers["UUID"])
            if is_authenticated:
                self.store_data(is_authenticated)
            else:
                self.respond(401)

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
        person = Person(json_data["Email"], json_data["Password"])
        self.respond(200, postbox.insert_person(person).encode('utf-8'))

    def sign_in(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        login_data = json.loads(data.decode('utf-8'))
        login_email = login_data["email"]
        sql_check = postbox.check_password(login_email, login_data["password"])
        if sql_check:
            session_id = uuid.uuid4().__str__()
            if login_email in session_IDs.values():
                for key, value in dict(session_IDs).items():
                    if value == login_email:
                        del session_IDs[key]
            session_IDs[session_id] = login_email
            signin_data = json.dumps({"UUID": session_id}, indent=2).encode()
            self.respond(200, signin_data
                         , {'Content-Type': 'application/json',
                            'Content-Length': len(signin_data).__str__()})
        else:
            self.respond(400, b"Sign in  Failed")

    def sign_out(self):
        if self.headers["UUID"] in session_IDs:
            del session_IDs[self.headers["UUID"]]
            self.respond(200, b"Signed out")
        else:
            self.respond(400, b'Not authenticated')

    def store_data(self, authentication):
        data = self.rfile.read(int(self.headers['Content-Length']))
        message = json.loads(data.decode("utf-8"))
        message["from_email"] = authentication
        postbox.insert_message(message)
        self.respond(200, b'Message sent')

    def fetch_messages(self, email):
        messages = make_json_data(postbox.fetch_messages_to_email(email))
        self.respond(200, messages, {'Content-Type': 'application/json'})

    def is_authorised(self):
        self.respond(400, b'Not authorized')

    def respond(self, code=200, response_message=None, headers=None):
        self.send_response(code)
        if headers:
            for header in headers:
                self.send_header(header, headers[header])
        self.end_headers()
        if response_message:
            self.wfile.write(response_message)

    def authenticate(self, session_id):
        if session_id not in session_IDs.keys():
            return False
        else:
            return session_IDs[session_id]


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
