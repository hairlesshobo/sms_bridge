#!/usr/bin/env python3

import json
import os
import serial
import string
import time

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

SERIAL_PORT = os.environ["SERIAL_PORT"] #"/dev/ttyUSB0"
LISTEN_PORT = os.getenv("LISTEN_PORT", "80")

AT_ESC = bytes([27])
AT_CTRL_Z = bytes([26])

app = FastAPI()

class SmsMessage(BaseModel):
    recipient: str
    message: str

class GsmModem:
    def connect(self):
        print("Connecting to modem...")
        self.ser = serial.Serial(SERIAL_PORT, 460800, timeout=5)
        time.sleep(0.25)


    def __current_milli_time(self):
        return round(time.time() * 1000)


    def __wait_for_response(self, expected_response, timeout=5):
        start_time = self.__current_milli_time()

        while (self.__current_milli_time() - start_time) < (timeout * 1000):
            data = self.ser.readline()
            
            # not sure why we get empty lines at the start of most reads, but this helps to speed things up
            # we read again if we got an empty response from the serial port
            if data.decode().strip() == '':
                data=self.ser.readline()

            response = data.decode()

            # print(f"response - '{response.rstrip()}'")
            if "error" in response.lower():
               print(f"ERROR: {response.rstrip()}")
               raise Exception

            if response.startswith(expected_response):
                return

            time.sleep(0.1)

        raise Exception


    def __send_cmd(self, command, response = None, timeout = 5):
        bcommand = bytes([0])

        if type(command) is bytes:
            bcommand = command

        if type(command) is str:
            for char in command:
                if char not in string.printable:
                    raise Exception

            # print(command)
            bcommand = command.encode()

        self.ser.write(bcommand)

        if response is not None:
            self.__wait_for_response(response, timeout)


    def send_sms(self, recipient: str, message: str):
        try:
            print(f"Recipient: {recipient}")
            print(f"Message: {message}")
            print("Sending message...")

            self.__send_cmd(AT_ESC)
            self.__send_cmd("ATE0\r", "OK")
            self.__send_cmd("AT+CMEE=2\r", "OK")
            self.__send_cmd("AT\r", "OK")
            self.__send_cmd("AT+CMGF=1\r", "OK")
            self.__send_cmd(f"AT+CMGS=\"{recipient}\"\r", ">")
            self.__send_cmd(f"{message}\r")
            self.__send_cmd(AT_CTRL_Z, "OK")
            print()
            print("Message sent successfully")
            print()
        except:
            print("Aborting operation")
            self.__send_cmd("\r")
            self.__send_cmd(AT_ESC)
            self.__send_cmd(AT_CTRL_Z)
            time.sleep(0.5)
            raise


    # TODO: make this work
    # def get_sms(self):
    #     print("Reading messages...")
    #     self.__send_cmd("AT\r", "OK")
    #     self.__send_cmd("AT+CMGF=1\r", "OK")
    #     self.__send_cmd("AT+CMGL=\"REC UNREAD\"\r")

    #     data = self.ser.readall()
    #     print(data.decode())

    #     print("Done reading messages...")


    def disconnect(self):
        print("Disconnecting from modem...")
        self.ser.close()



@app.post("/send_sms/")
async def create_item(payload: SmsMessage):
    try:
        modem = GsmModem()
        modem.connect()
        modem.send_sms(payload.recipient, payload.message)
        modem.disconnect()
    except:
        return {"result": "FAIL"}
    
    return {"result": "SUCCESS"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(LISTEN_PORT))
