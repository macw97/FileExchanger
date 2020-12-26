import socket
import logging
import os

SERVER_PORT=5000
BUFFER_SIZE=4096
def get_logger_file(name,file_path,log_level):
    log_file=logging.getLogger(name)
    log_file.setLevel(log_level)
    handler=logging.FileHandler(file_path)
    handler_format=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(handler_format)
    log_file.addHandler(handler)
    return log_file

def socket_error_handler(exception_msg,exception_place,fd_socket,logger):
    logger.error("%s : %s".format(exception_place,exception_msg))


class Server:
    def __init__(self,ip_address,port,log_file):
        self.ip_address=ip_address
        self.port=port

    def start(self):
        log_file.info("Server started")
        try:
            log_file.debug("Server_start(): Create socket")
            fd_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error as msg:
            socket_error_handler(msg,'Server_start()',fd_socket,log_file)
        try:
            log_file.debug("Server_start(): set socket option")
            fd_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except socket.error as msg:
            socket_error_handler(msg,'Server_start()',fd_socket,log_file)
        try:
            log_file.debug("Server_start(): socket bind ")
            fd_socket.bind((self.ip_address,self.port))
        except socket.error as msg:
            socket_error_handler(msg,'Server_start()',fd_socket,log_file)
        fd_socket.listen(3)
        client_socket, address=fd_socket.accept()
        print(f"{address} is connected.")
        received=client_socket.recv(BUFFER_SIZE).decode()
        filename,filesize=received.split(":")
        filename=os.path.basename(filename)
        filesize=int(filesize)
        reading=True
        with open(filename,"wb") as file:
            while reading :
                byte_read=client_socket.recv(BUFFER_SIZE)
                if not byte_read:
                    reading=False
                    break
                file.write(byte_read)
        client_socket.close()
        log_file.debug("Server_start(): ended download from client")
        fd_socket.close()





if __name__ == "__main__":
    log_file=get_logger_file("log_operations","/var/log/server.log",logging.DEBUG)
    first_server=Server("0.0.0.0",SERVER_PORT,log_file)
    first_server.start()


