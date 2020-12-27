import socket
import logging
import os
import sys
import time
import atexit
import select

PORT=5000
BUFFER_SIZE=4096

def get_logger_file(name,file_path,log_level):
    log_file=logging.getLogger(name)
    log_file.setLevel(log_level)
    handler=logging.FileHandler(file_path)
    handler_format=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(handler_format)
    log_file.addHandler(handler)
    return log_file

def recv_file(client_socket,filename):
    with open(filename,"wb") as file:
            while True :
                byte_read=client_socket.recv(BUFFER_SIZE)
                if not byte_read:
                    reading=False
                    break
                file.write(byte_read)
class Daemon:
    def __init__(self,pidfile):
        self.pidfile=pidfile

    def daemonize(self):
        # Fork and exit first parent process
        try:
            pid=os.fork()
            if pid>0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # disconnect from parent environment
        # os.chdir("/")
        os.setsid()
        os.umask(0)

        # Second fork
        try:
            pid=os.fork()
            if pid>0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n' .format(err))
            sys.exit(1)
        
        # Redirect standard files in/out/err
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull,'r')
        so = open(os.devnull,'a+')
        se = open(os.devnull, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile,'w+') as file:
            file.write(pid+'\n')
    
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        # Check for a pidfile to see if deamon already runs
        try:
            with open(self.pidfile,'r') as pfile:
                pid = int(pfile.read().strip())
            
        except IOError:
            pid = None
        if pid:
            message = "pidfile {0} already exist." + \
                "Daemon already running?\n"
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)

        self.daemonize()
        self.run()

    def run(self):
        raise NotImplementedError

class Server(Daemon):
    def __init__(self,ip_address,port):
        super().__init__('/tmp/deamon-test.pid')
        self.ip_address=ip_address
        self.port=port
        self.log_file=get_logger_file("log_operations","/var/log/server.log",logging.DEBUG)
    
    def socket_error_handler(exception_msg,exception_place,fd_socket):
        self.log_file.error("%s : %s".format(exception_place,exception_msg))
        sys.exit(1)

    def run(self):
        self.log_file.info("Server_run(): Server started")
        try:
            self.log_file.debug("Server_run(): Create socket")
            fd_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error as msg:
            socket_error_handler(msg,'Server_run()',fd_socket,log_file)
        try:
            self.log_file.debug("Server_run(): set socket option")
            fd_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except socket.error as msg:
            socket_error_handler(msg,'Server_start()',fd_socket,log_file)
        try:
            self.log_file.debug("Server_run(): socket bind ")
            fd_socket.bind((self.ip_address,self.port))
        except socket.error as msg:
            socket_error_handler(msg,'Server_run()',fd_socket,log_file)
        fd_socket.listen(3)
        # setting server socket nonblocking 
        fd_socket.setblocking(False)

        # epoll object creation
        epoll = select.epoll()
        epoll.register(fd_socket.fileno(),select.EPOLLIN | select.EPOLLOUT)

        try: 
            connections={}
            requests={}
            responses={}
            firstMessage={}
            while True:
                # waiting up to 30 seconds for event to occure and return query epoll object 
                events = epoll.poll(30)
                for fileno, event in events:
                    # if event occurse on the server socket then a new socket connection show up
                    if fileno == fd_socket.fileno():
                        self.log_file.info("Server_run(): new connection found")
                        connection, address = fd_socket.accept()
                        connection.setblocking(False)
                        epoll.register(connection.fileno(),select.EPOLLIN | select.EPOLLOUT)
                        connections[connection.fileno()] = connection
                        requests[connection.fileno()] =''
                        responses[connection.fileno()] =''
                        firstMessage[connection.fileno()] = True
                        self.log_file.info("Server_run(): connection {0} added to epoll".format(address))
                    elif event & select.EPOLLIN:
                        # read data because EPOLLIN event occured
                        if firstMessage[fileno] == True :
                            filename=connections[fileno].recv(BUFFER_SIZE).decode()
                            self.log_file.info("Server_run(): received message/data - {0}".format(filename))
                            filename=os.path.basename(filename)
                            self.log_file.info("Server_run(): download file {0}".format(filename))
                            recv_file(connections[fileno],filename)
                            self.log_file.info("Server_run(): fileno = {0} ended downloading file {1}".format(fileno,filename))
                            firstMessage[fileno] = False
                    elif event & select.EPOLLOUT:
                        # write data because EPOLLOUT event occured
                        byteswritten = connections[fileno].send(responses[fileno])
                        responses[fileno] = responses[fileno][byteswritten:]
                        self.log_file.info("Server_run(): write message/data - {0}".format(responses[fileno]))
                    elif event & select.EPOLLHUP:
                        # delete socket connection from epoll because client hang up
                        epoll.unregister(fileno)
                        self.log_file.info("Server_run(): fileno = {0} unregister from epoll".format(fileno))
                        connections[fileno].close()
                        del connections[fileno]
        finally:
            epoll.unregister(fd_socket.fileno())
            epoll.close()
            fd_socket.close()



if __name__ == "__main__":
    first_server=Server("0.0.0.0",PORT)
    first_server.start()


