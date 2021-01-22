import socket
import logging
import sys
import os
import time
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import Tlv_block.py as tlv

BUFFER_SIZE=4096
TLV_SIZE = 6
PORT=5000

def IP_validation(address):
    try:
        socket.inet_aton(address)
    except socket.error as msg:
        print('Address is not IPv4 : {0}'.format(msg))
        return False
    return True

def read_and_send(client_socket,filename):
     with open(filename,"rb") as file:
            while True:
                byte_read=file.read(BUFFER_SIZE)
                print(byte_read)
                if not  byte_read:
                    break
                client_socket.send(byte_read)

def recv_file(client_socket,filename):
    tlv_data = client_socket.recv(TLV_SIZE)
    tlv_decoded = tlv.decode_tlv(tlv_data)
    if tlv_decoded[2] == 0:
        print("File does not exist or is empty")
        return
    size = tlv_decoded[2]
    bytes_received = 0
    with open(filename,"wb") as file:
            while bytes_received < size :
                byte_read = client_socket.recv(BUFFER_SIZE)
                bytes_received += len(byte_read)
                print(byte_read)
                file.write(byte_read)
    if os.stat(filename).st_size == 0:
        print("File does not exist or is empty")
        os.remove(filename)

def get_list_directory(client_socket):
    list_directory = ""
    while True:
        byte_read = client_socket.recv(BUFFER_SIZE)
        if b'\r\n\r' in byte_read:
            byte_read = byte_read[0: len(byte_read)-3]
            list_directory += byte_read.decode("utf-8")
            break
        list_directory += byte_read.decode("utf-8")
    print(list_directory)

def remove_file_info(client_socket):
    byte_read = client_socket.recv(BUFFER_SIZE)
    print(byte_read.decode("utf-8"))

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
        elif len(self.command.split()) == 2 and self.command.lower().split()[0] == 'rm':
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
            if len(self.command.split()) == 1:
                tlv_data = tlv.Tlv_block(self.command)
                client_socket.send(tlv_data.tlv)
                if tlv_data.tvl[0] == 3: #list_directory
                    get_list_directory(client_socket)
                elif tlv_data.tvl[0] == 5: #close
                    print('Closing socket\n')
            elif len(self.command.split()) == 2:
                tlv_data = tlv.Tlv_block(self.command.split()[0], self.command.split()[1])
                client_socket.send(tlv_data.tlv)
                client_socket.send(self.command.split()[1])
                if tlv_data.tvl[0] == 1: #send
                    read_and_send(client_socket, command.split()[1])
                elif tlv_data.tvl[0] == 2: #download
                    recv_file(client_socket, command.split()[1])
                elif tlv_data.tvl[0] == 4: #rm
                    remove_file_info(client_socket, command.split()[1])
                
        client_socket.close()



if __name__ == "__main__":
    print(f"Script arugment: {sys.argv[1]}")
    if IP_validation(sys.argv[1]) :
        first_Client=Client(sys.argv[1],PORT)
        first_Client.run()
