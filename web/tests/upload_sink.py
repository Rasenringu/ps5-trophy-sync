"""Isolated MOCK upload receiver; no auth, database, console or real UCP parsing."""
import hashlib
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Sink(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, value):
        raw=json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.reply(200, {'status':'MOCK-ready'})

    def do_POST(self):
        if self.path!='/device/artwork':
            self.reply(404,{});return
        expected=int(self.headers.get('Content-Length','0'))
        if expected>64*1024*1024:
            self.reply(413,{});return
        self.connection.settimeout(3)
        used=0;digest=hashlib.sha256()
        try:
            while used<expected:
                data=self.rfile.read(min(65536,expected-used))
                if not data:break
                used+=len(data);digest.update(data)
        except (socket.timeout,ConnectionError):
            pass
        result={'mock':True,'received':used,'expected':expected,'sha256':digest.hexdigest()}
        print(json.dumps(result),flush=True)
        self.reply(200 if used==expected else 400,result)

ThreadingHTTPServer(('0.0.0.0',8000),Sink).serve_forever()
