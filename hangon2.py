#/usr/bin/env python
import pymodbus
import serial
import socket
import errno
import time
import json
import struct
import os
from pymodbus.client.sync import ModbusSerialClient
# from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import ConfigParser
#real device num : fms device num
#device_num = {'20':1}
device_num={'1':1,'2':2}
global sock
global sock_sub
global main_ser_ip
global main_ser_port
global sub_ser_ip
global sub_ser_port
global server_id
global dev_type
global floor

device_info={}

def init():
        global main_ser_ip
        global main_ser_port
        global sub_ser_ip
        global sub_ser_port
        global server_id
        global dev_type
        global floor
        global device_num
        global device_info

        config=ConfigParser.ConfigParser()
        config.read('config.ini')

        main_ser_ip=str(config.get('SERVER1','ip'))
        main_ser_port=int(config.get('SERVER1','port'))
        sub_ser_ip=str(config.get('SERVER2','ip'))
        sub_ser_port=int(config.get('SERVER2','port'))

        server_id = int(config.get('DEV_INFO','server_id'))
        floor = int(config.get('DEV_INFO','floor'))
        dev_type = int(config.get('DEV_INFO','dev_type'))

        f = open('/home/pi/fms/hangon/dev_type','r')

        for x in f:
                if x[0]=='#' or x[0]=='\n':
                        continue
                k, v, h = x.strip('\n').split(':')
                device_num[v]=int(k)
                device_info[v]=h
                #print (device_num)
                #print (device_info)



def process_color_AAA(rr, dev_num) :
    if rr.isError():
        return False
    else:
        try:
            systemstatus = str(rr.registers[47]) # b0100101
            print("systemstatus : " + systemstatus)
            print("binary : " + str(bin(rr.registers[47])))
            print("binary split : " + str(bin(rr.registers[47])).split("b")[1])
            aftersystemstatus = ""
            for i in range(0, 16 - len(str(bin(rr.registers[47])).split("b")[1])):
                aftersystemstatus += "0"

            aftersystemstatus = aftersystemstatus + str(bin(rr.registers[47])).split("b")[1]
                # 0000000000000000
                # 0000000000101010
            oper_stat = int(aftersystemstatus[len(aftersystemstatus) - 1]) + 1 # 0bit
            cs1 = int(aftersystemstatus[len(aftersystemstatus) - 2]) + 1 # 1bit

            alramstatus = str(rr.registers[48])

            afteralramstatus = ""
            for i in range(0, 16 - len(str(bin(rr.registers[48])).split("b")[1])):
                afteralramstatus += "0"
            afteralramstatus = afteralramstatus + str(bin(rr.registers[48])).split("b")[1]

            arm_fan = int(afteralramstatus[len(afteralramstatus) - 1]) + 1# 0bit
            arm_comp1 = int(afteralramstatus[len(afteralramstatus) - 2]) + 1# 1bit
            arm_comp2 = int(afteralramstatus[len(afteralramstatus) - 3]) + 1 # 2bit
            arm_leak = int(afteralramstatus[len(afteralramstatus) - 7]) + 1 # 6bit
            
            arm_temperature_senser = int(afteralramstatus[len(afteralramstatus) - 8]) + 1 # 7bit

            arm_high_tmp = int(afteralramstatus[len(afteralramstatus) - 10]) + 1 # 9bit
            temp = float(rr.registers[58]) / 10.0

            data = {
                "server_id":server_id,"dev_type":1,"dev_num":dev_num,
                "oper_stat":oper_stat,"cs1":cs1,
                "arm_fan":arm_fan,"arm_comp1":arm_comp1,
                "arm_comp2":arm_comp2,"arm_leak":arm_leak,"arm_temperature_senser":arm_temperature_senser,
                "arm_high_tmp":arm_high_tmp,"temp":temp,"link":1,"floor": floor,
            }
            return data
        except Exception as e:
            print(e)
            #data ={"dev_type": 1, "server_id": server_id, "dev_num": dev_num, "link": 2, "floor": floor}
            data =False
            return data 

def processing(client):
    for i in range(0, 3):
    #while(1):
        for dev_id in device_info:
            if device_info.get(dev_id) == 'color_AAA':
                print(device_num.get(dev_id))
                result = client.read_holding_registers(address=200,count=68,unit=device_num.get(dev_id))    

                if result.isError():
                    data = process_color_AAA(result, device_num.get(dev_id))
                else:
                    result2 =result.registers
                    data = process_color_AAA(result, device_num.get(dev_id))
                    # print(str(data))
                print(data)
                if data==False:
                    print('false')
                else : 
                    resultCommand = 'echo ' + str(data) + ' > color_AAA'
                    os.system(resultCommand)


def main():
    init()
    client=ModbusSerialClient(method = "rtu", port = "/dev/ttyUSB0",timeout=0.5, stopbits=1,bytesize=8,parity='N',baudrate=9600,strict=False)
    connection = client.connect()

    processing(client)
    client.close()

main()