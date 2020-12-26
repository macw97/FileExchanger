import socket
import logging
import sys
import os

BUFFER_SIZE=4096
class Client:
    def __init__(self,ip_address,port,file_name):
        self.ip_address=ip_address
        self.port=port
        self.file_name=file_name

    def start(self):
        client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        print(f"Server address : {self.ip_address} file to send : {self.file_name}")
        client_socket.connect((self.ip_address,self.port))
        size=os.path.getsize(self.file_name)
        print(f"Message {self.file_name}:{size}")
        client_socket.send(f"{self.file_name}:{size}".encode())
        reading=True
        with open(self.file_name,"rb") as file:
            while reading:
                byte_read=file.read(BUFFER_SIZE)
                if not byte_read:
                    reading=False
                    break
                client_socket.sendall(byte_read)
            
        client_socket.close()



if __name__ == "__main__":
    print(f"Script arugment: {sys.argv[1]}")
    print(f"File to send : {sys.argv[2]}")
    first_Client=Client(sys.argv[1],5000,sys.argv[2])
    first_Client.start()
