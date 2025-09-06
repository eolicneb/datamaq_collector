import importlib
import os
from dotenv import load_dotenv

from serial.tools import list_ports


load_dotenv()

if fake_serial:=os.getenv('FAKE_SERIAL'):
    ser_name, ser_package = map("".join, map(reversed, "".join(reversed(fake_serial)).split(".", 1)))
    FakeSerial_module = importlib.import_module(ser_package)
    FakeSerial = getattr(FakeSerial_module, ser_name, None)
else:
    FakeSerial = None


def get_com_ports():
    comports = list(list_ports.comports())
    if FakeSerial:
        device_description = os.getenv('FAKE_DEVICE_DESCRIPTION', "")
        comports += [(FakeSerial("COM-F"), device_description, None)]

    return comports
