from dataclasses import dataclass
from random import randint

import crcmod


def crc16(data):
    return crcmod.predefined.mkCrcFun('modbus')(data).to_bytes(2, byteorder='little')


@dataclass
class Request:
    id: int = None
    code: int = None
    addr: int = None
    regs: int = None

    @property
    def count(self):
        return self.regs * (2 if self.code == 3 else 1)


class FakeSerial:
    def __init__(self, port="COM-F", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.request = Request()

    def open(self, *args, **kwargs):
        print(f"open method - args: {args}, kwargs: {kwargs}")

    def close(self, *args, **kwargs):
        print(f"close method - args: {args}, kwargs: {kwargs}")

    def read(self, reading_bytes):
        # bytes_hex = input(f"read method - mode={mode} - {self.request.count} bytes > ")
        # new_bytes = bytes.fromhex(bytes_hex)
        new_bytes = randint(0, (256**self.request.count)-1).to_bytes(self.request.count)
        chopped_bytes = (new_bytes * self.request.count)[:self.request.count]
        header = ((self.request.id << 8*2) + (self.request.code << 8) + self.request.count).to_bytes(3)
        message = header + chopped_bytes
        assert len(message) == reading_bytes - 2, f"Message length ({len(message)}) is wrong. Should be {reading_bytes - 2}"
        print(f"Forwarding bytes ({chopped_bytes}) for length {reading_bytes} as {message} <h-{message.hex()}>")
        return message + crc16(message)

    def write(self, instruction, *args, **kwargs):
        self.request.id = instruction[0]
        self.request.code = instruction[1]
        self.request.addr = int.from_bytes(instruction[2:4])
        self.request.regs = int.from_bytes(instruction[4:6])
        print(f"write method - instruction: {instruction}, request: {self.request} args: {args}, kwargs: {kwargs}")

    def is_open(self, *args, **kwargs):
        print(f"is_open method - args: {args}, kwargs: {kwargs}")
        return True

    def reset_input_buffer(self):
        print(f"Resetting serial input buffer in {self.port}")

    def reset_output_buffer(self):
        print(f"Resetting serial output buffer in {self.port}")
