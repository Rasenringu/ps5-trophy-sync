"""LOCAL controlled TLS fixtures; no console or service credentials."""
import json,socket,ssl,subprocess,sys,threading
from pathlib import Path
root=Path(__file__).resolve().parents[2]
identity=json.loads((root/'.local/tls/identity.json').read_text())
certs=list((root/'.local/tls').glob('server.crt'))
assert certs
context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(str(certs[0]),str(root/'.local/tls/server.key'))
client,=sys.argv[1:]
def attempt(response,name=None,ca=None,host="127.0.0.1"):
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(5)
    errors=[]
    def serve():
        try:
            raw,_=listener.accept()
            with context.wrap_socket(raw,server_side=True) as peer:
                request=b''
                while b'\r\n\r\n' not in request:request+=peer.recv(4096)
                assert request.startswith(b'POST /api/device/status HTTP/1.1\r\n')
                assert b'Authorization:' not in request
                headers,body_in=request.split(b'\r\n\r\n',1)
                assert b'Content-Type: application/octet-stream' in headers
                length=int(next(line.split(b':',1)[1] for line in headers.split(b'\r\n') if line.lower().startswith(b'content-length:')))
                while len(body_in)<length:body_in+=peer.recv(min(65536,length-len(body_in)))
                assert body_in==b'A'*(2*1024*1024+327)
                peer.sendall(response)
        except (ssl.SSLError,ConnectionError,OSError):pass
        except Exception as e:errors.append(e)
        finally:listener.close()
    worker=threading.Thread(target=serve,daemon=True);worker.start()
    output=subprocess.check_output([client,str(listener.getsockname()[1]),name or identity['server_ip'],str(ca or root/'.local/tls/ca.crt'),'/api/device/status',host],text=True,timeout=20)
    worker.join(timeout=6);assert not worker.is_alive() and not errors,errors
    return [int(x) for x in output.split()]
body=b'{"status":"MOCK"}'
good=b'HTTP/1.1 200 OK\r\nContent-Length: '+str(len(body)).encode()+b'\r\nConnection: close\r\n\r\n'+body
assert attempt(good)==[0,0,1,200,len(body)]
assert attempt(good,host="localhost")==[0,0,1,200,len(body)]
for invalid in [
    b'HTTP/1.1 200 OK\r\nContent-Length: 8\r\nContent-Length: 8\r\n\r\n{}',
    b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n2\r\n{}\r\n0\r\n\r\n',
    b'HTTP/1.1 200 OK\r\nContent-Length: 9\r\n\r\n{}',
    b'HTTP/1.1 200 OK\r\nContent-Length: 16384\r\n\r\n',
    b'HTTP/1.1 200 OK\r\nContent-Length: -1\r\n\r\n',
    b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n{}',
]:
    result=attempt(invalid);assert result[0]!=0 and result[4]==0,result
result=attempt(good,'wrong-host.invalid');assert result[0]!=0 and not result[2]
redirect=b'HTTP/1.1 302 Found\r\nContent-Length: 2\r\nLocation: http://example.invalid\r\n\r\n{}'
assert attempt(redirect)==[0,0,1,302,2]
print('PASS LOCAL JSON TLS: certificate/name, bounded body, truncation, duplicate/invalid/missing length, chunked refusal, no redirects.')
