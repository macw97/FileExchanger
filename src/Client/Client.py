import socket
import logging
import sys
import os

BUFFER_SIZE=4096
PORT=5000

def read_and_send(client_socket,filename):
     with open(filename,"rb") as file:
            while True:
                byte_read=file.read(BUFFER_SIZE)
                if not byte_read:
                    reading=False
                    break
                client_socket.sendall(byte_read)
            

class Client:
    def __init__(self,ip_address,port,file_name):
        self.ip_address=ip_address
        self.port=port
        self.file_name=file_name

    def socket_error_handler(self,exception_msg,exception_place,fd_socket):
        print("{0} : {1}".format(exception_place,exception_msg))
        sys.exit(1)

    def start(self):
        try:
            client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_start()',client_socket)
        try:
            client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_start()',client_socket)
        print(f"Server address : {self.ip_address} file to send : {self.file_name}")
        try:
            client_socket.connect((self.ip_address,self.port))
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_start()',client_socket)
        print(f"Message {self.file_name}")
        try:
            client_socket.send(f"{self.file_name}".encode())
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_start()',client_socket)
        read_and_send(client_socket,self.file_name)
        client_socket.close()



if __name__ == "__main__":
    print(f"Script arugment: {sys.argv[1]}")
    print(f"File to send : {sys.argv[2]}")
    first_Client=Client(sys.argv[1],PORT,sys.argv[2])
    first_Client.start()
