import os

class Tlv_block:
    def __init__(self, cmd, file = ""):
        type = 0
        if cmd == "send": type = 1
        elif cmd == "download": type = 2
        elif cmd == "list_directory": type = 3
        elif cmd == "rm": type = 4
        elif cmd == "close": type = 5
        length = 0
        value = 0
        if file:
            length = len(file)
            if os.path.isfile(file) and cmd != "rm":
                value = os.path.getsize(file)
        b_type = type.to_bytes(1, 'big')
        b_length = length.to_bytes(1, 'big')
        b_value = value.to_bytes(4, 'big')
        self.tlv = b_type + b_length + b_value

def decode_tlv(data):
    type = data.tlv[0]
    length = data.tlv[1]
    value = int.from_bytes(data.tlv[2:6], 'big')
    return (cmd, length, value)
