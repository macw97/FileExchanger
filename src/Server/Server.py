import socket
import logging
import os
import sys
import time
import atexit
import select
import random

PORT=5000
BUFFER_SIZE=4096

def find_newline(bytes):
    for b in range(len(bytes)):
        print(bytes[b])
        if bytes[b] == 10:
            return b
    return len(bytes)

def get_logger_file(name,file_path,log_level):
    log_file=logging.getLogger(name)
    log_file.setLevel(log_level)
    # mode = write provides logging for only this run of program
    handler=logging.FileHandler(file_path, mode ='w')
    handler_format=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(handler_format)
    log_file.addHandler(handler)
    return log_file

def read_and_send(client_socket, filename, logger):
    logger.debug("read_and_send() Started sending file {0}".format(filename))
    if not os.path.isfile(filename):
        client_socket.send(b'\r\n\r')
        logger.debug("read_and_send() Attempt to download file {0} failed, file does not exist".format(filename))
        return
    with open(filename, "rb") as file:
        byte_read = file.read(BUFFER_SIZE)
        while byte_read:
            logger.debug("read_and_send() sending  {0}".format(byte_read))
            client_socket.send(byte_read)
            byte_read = file.read(BUFFER_SIZE)
    client_socket.send(b'\r\n\r')
    logger.debug("read_and_send() Finished sending file {0}".format(filename))


def recv_file(client_socket,filename,logger, buff):
    logger.debug("recv_file(): Started download file {0}".format(filename))
    with open(filename,"wb") as file:
        file.write(buff)
        while True :
            try:
                byte_read=client_socket.recv(BUFFER_SIZE)
                logger.debug("recv_file(): download {0}".format(byte_read))
                file.write(byte_read)
                logger.debug("recv_file(): write to file")
            except:
                logger.debug("recv_file(): end of download")
                break

def send_list_directory(client_socket, logger):
    logger.debug("send_list_directory(): Creating list")
    list_directory = os.listdir()
    for file in list_directory:
        if file == 'Server.py':
            continue
        client_socket.send(file.encode("utf-8"))
        client_socket.send(b'\n')
    client_socket.send(b'\r\n\r')

def remove_file(client_socket, filename, logger):
    try:
        os.remove(filename)
        client_socket.send(b'file succesfuly removed')
        logger.debug("remove_file(): file succesfuly removed")
    except:
        client_socket.send(b'file does not exist')
        logger.debug("remove_file(): file does not exist")


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
        # Creating/opening log file and erasing content  
        self.log_file=get_logger_file("log_operations","/var/log/server.log",logging.DEBUG)
        self.log_file
    
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
        fd_socket.listen(1)
        # setting server socket nonblocking 
        fd_socket.setblocking(False)

        # epoll object creation
        epoll = select.epoll()
        epoll.register(fd_socket.fileno(),select.EPOLLIN)
        self.log_file.debug("Server_run(): epoll object created")
        # each client gets unique Id
        unique_id_array=list(range(100,150))
        random.shuffle(unique_id_array)
        self.log_file.debug("Server_run(): unique ids prepared")
        i=0
        try: 
            connections={}
            id={}
            requests={}
            responses={}
            while True:
                # waiting up to 60 seconds for event to occure and return query epoll object
                events = epoll.poll(60)
                for fileno, event in events:
                    # if event occurse on the server socket then a new socket connection show up
                    if fileno == fd_socket.fileno():
                        self.log_file.info("Server_run(): new connection found")
                        connection, address = fd_socket.accept()
                        connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                        connection.setblocking(False)
                        connections[connection.fileno()] = connection
                        id[connection.fileno()]=unique_id_array[i]
                        i=i+1
                        requests[connection.fileno()] =''
                        responses[connection.fileno()] =''
                        epoll.register(connection.fileno(),select.EPOLLIN)
                        self.log_file.info("Server_run(): connection {0} added to epoll with id - {1}".format(address,id[connection.fileno()]))
                    elif event & select.EPOLLIN:
                        # read data because EPOLLIN event occured
                        self.log_file.info("Server_run(): EPOLLIN occured id - {0}".format(id[fileno]))
                        requests[fileno]=connections[fileno].recv(BUFFER_SIZE)
                        self.log_file.info("Server_run(): id - {0} received message - {1}".format(id[fileno],requests[fileno]))
                        if requests[fileno] == b'list_directory':
                            send_list_directory(connections[fileno], self.log_file)
                            self.log_file.info("Server_run(): id - {0} list directory sent".format(id[fileno]))
                        elif requests[fileno] == b'close':
                            epoll.unregister(fileno)
                            self.log_file.info("Server_run(): id - {0} unregister from epoll".format(id[fileno]))
                            connections[fileno].close()
                            del connections[fileno]
                            del id[fileno]
                        else:
                            endl = find_newline(requests[fileno])
                            req = requests[fileno][0:endl]
                            buff = requests[fileno][endl + 1 :]
                            self.log_file.info("Server_run(): buff - {0}".format(buff))
                            (cmd , filename) = req.split()
                            filename = os.path.basename(filename)
                            if cmd == b'send':
                                self.log_file.info("Server_run(): id - {0} do {1} file {2}".format(id[fileno],cmd,filename))
                                recv_file(connections[fileno],filename,self.log_file, buff)
                                self.log_file.info("Server_run(): id - {0} ended downloading file {1}".format(id[fileno],filename))
                            elif cmd == b'download':
                                self.log_file.info("Server_run(): id - {0} send file - {1}".format(id[fileno],requests[fileno].split()[1]))
                                read_and_send(connections[fileno],requests[fileno].split()[1].decode("utf-8"), self.log_file)
                            elif cmd == b'rm':
                                self.log_file.info("Server_run(): id - {0} send request to remove file - {1}".format(id[fileno],requests[fileno].split()[1]))
                                remove_file(connections[fileno], filename, self.log_file)
                    elif event & select.EPOLLOUT:
                        # write data because EPOLLOUT event occured. Add ls command 
                        pass
                    elif event & select.EPOLLHUP:
                        # delete socket connection from epoll because client hang up
                        pass
        finally:
            epoll.unregister(fd_socket.fileno())            
            epoll.close()
            self.log_file.info("Server_run(): server closed")
            fd_socket.close()



if __name__ == "__main__":
    first_server=Server("0.0.0.0",PORT)
    first_server.start()


