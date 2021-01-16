import socket
import logging
import sys
import os
import time

BUFFER_SIZE=4096
PORT=5000

def IP_validation(address):
    try:
        socket.inet_aton(address)
    except socket.error as msg:
        print('Address is not IPv4 : {0}'.format(msg))
        return False
    return True
"""
Funkcje read and send nie dzialaja i recv file
"""
def read_and_send(client_socket,filename):
     with open(filename,"rb") as file:
            while True:
                byte_read=file.read(BUFFER_SIZE)
                print(byte_read)
                if not  byte_read:
                    break
                client_socket.send(byte_read)

def recv_file(client_socket,filename):
    with open(filename,"wb") as file:
            while True :
                byte_read = client_socket.recv(BUFFER_SIZE)
                print(byte_read)
                if b'\r\n\r' in byte_read:
                    byte_read = byte_read[0: len(byte_read)-6]
                    file.write(byte_read)
                    break
                file.write(byte_read)
            
class Client:
    def __init__(self,ip_address,port):
        self.ip_address=ip_address
        self.port=port
        self.command=''

    def socket_error_handler(self,exception_msg,exception_place,fd_socket):
        print("{0} : {1}".format(exception_place,exception_msg))
        sys.exit(1)

    def print_commands(self):
        print('Commands man:\n')
        print('send - \n')
        print('download - \n')
        print('ls - \n')
        print('help - \n')
        print('rm - \n')

    def handleCmd(self):
        if self.command =='':
            print('No command provided\n')
            return ''
        elif self.command.lower() == 'help':
            self.print_commands()
            return ''
        elif self.command.lower() == 'ls':
            return 'list_directory'
        elif self.command.lower() == 'close':
            return self.command.lower()
        elif len(self.command.split()) == 2 and self.command.lower().split()[0] == 'send':
            if os.path.exists(self.command.split()[1]) :
                return self.command
            else :
                print('File doesn\'t exist\n')
                return ''
        elif len(self.command.split()) == 2 and self.command.lower().split()[0] == 'download':
            return self.command
        else :
              return ''

    def run(self):
        try:
            client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_run()',client_socket)
        try:
            client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_run()',client_socket)
        print(f"Server address : {self.ip_address}")
        try:
            client_socket.connect((self.ip_address,self.port))
        except socket.error as msg:
            self.socket_error_handler(msg,'Client_run()',client_socket)

        while self.command!='close':
            print("Type a command")
            self.command = ''
            self.command = input()
            self.command = self.handleCmd()
            print("Provided command: ", self.command)
            if self.command =='':
                continue
            elif self.command == 'close':
                print('Closing socket\n')
            else :
                try: 
                    print("Message send: {0}".format(self.command))
                    client_socket.send(self.command.encode())
                except socket.error as error:
                    self.socket_error_handler(msg,'Client_run()',client_socket)

                if len(self.command.split()) == 2 :
                    if self.command.lower().split()[0] == 'send' :
                        read_and_send(client_socket,self.command.split()[1])
                    elif self.command.lower().split()[0] == 'download' :
                        recv_file(client_socket,self.command.split()[1])
                else :
                    pass
        
        client_socket.close()



if __name__ == "__main__":
    print(f"Script arugment: {sys.argv[1]}")
    if IP_validation(sys.argv[1]) :
        first_Client=Client(sys.argv[1],PORT)
        first_Client.run()
