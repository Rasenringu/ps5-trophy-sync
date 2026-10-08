"""Synthetic local FTP fixtures; never a console result."""
import os,socket,subprocess,sys,threading

def attempt(listing,version='v0.21.1'):
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(4)
    errors=[]
    def serve():
        passive=None
        try:
            control,_=server.accept()
            with control:
                control.settimeout(4);stream=control.makefile('rb')
                control.sendall(('220-MOCK FTP\r\n220-Version: '+version+' (MOCK)\r\n220 Ready\r\n').encode())
                if version!='v0.21.1':return
                assert stream.readline()==b'USER anonymous\r\n';control.sendall(b'331 Password\r\n')
                assert stream.readline()==b'PASS anonymous\r\n';control.sendall(b'230 OK\r\n')
                assert stream.readline()==b'CWD /user/home/00000009/trophy2/nobackup/data\r\n';control.sendall(b'250 OK\r\n')
                assert stream.readline()==b'PASV\r\n';passive=socket.socket();passive.bind(('127.0.0.1',0));passive.listen(1);passive.settimeout(4)
                port=passive.getsockname()[1];control.sendall(f'227 MOCK (203,0,113,7,{port//256},{port%256}).\r\n'.encode())
                data,_=passive.accept()
                assert stream.readline()==b'MLSD\r\n';control.sendall(b'150 OK\r\n')
                with data:data.sendall(listing)
                control.sendall(b'226 Complete\r\n')
        except Exception as error:errors.append(error)
        finally:
            if passive:passive.close()
            server.close()
    thread=threading.Thread(target=serve);thread.start()
    env={**os.environ,'MOCK_FTP_PORT':str(server.getsockname()[1])}
    result=subprocess.run([sys.argv[1]],env=env,capture_output=True,text=True,check=True,timeout=20)
    thread.join(5);assert not thread.is_alive() and not errors,errors
    return result.stdout.splitlines()
rows=b'type=dir;size=0; NPWR12345_00\r\ntype=dir;size=0; NPWR12345_00\r\ntype=file;size=0; NPWR23456_00\r\ntype=dir;size=0; ../NPWR23456_00\r\ntype=dir;size=0; NPWR23456_00\r\n'
assert attempt(rows)==['0 2','NPWR12345_00','NPWR23456_00']
assert attempt(rows,'v0.22.0')==['-2 0']
assert attempt(b'type=dir; NPWR12345_00')==['-10 0']
assert attempt(b''.join(f'type=dir; NPWR{i:05d}_00\r\n'.encode() for i in range(129)))==['-10 0']
print('PASS LOCAL discovery: pinned banner, exact selected-profile path, loopback-only passive connection, native names/directories, deduplication, malformed/overflow refusal.')
