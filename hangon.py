#!/usr/bin/env python3
import serial
import time
import sys
import json

import socket
import errno

import struct
import configparser

import os
import datetime
#device info
#ex) 'd':'old' -> d : device number is 4      a:1 b:2 ... z:26
#ex)           -> old : old type device : black and white monitor
#ex)           -> new : new type device : color monitor
#ex) device_info={'d':'old', 'c':'new'}

#device_info={'a':'old','b':'old','c':'old','d':'old','e':'old','f':'old'}
#device_num ={'a':7,'b':2,'c':3,'d':4,'e':5,'f':6}
#device_info={'a':'color'}
#port = "/dev/ttyUSB0"

device_num={}
device_info={}

#check_sum
#input read_byte.
#sum all byte from 0 to 55
#black and white monitor

#sock fd
global sock
global sock_sub

global main_ser_ip
global main_ser_port
global sub_ser_ip
global sub_ser_port
global server_id
global dev_type
global floor

def write_pid(str):
        f=open('/home/pi/fms/hangon/result','a')
        f.write('{} time{}   pid{}\n'.format( str ,datetime.datetime.now(), os.getpid()))
        f.close()

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

        config=configparser.ConfigParser()
        config.read('/home/pi/fms/hangon/config.ini')
        #config.read('./config.ini')

        main_ser_ip=str(config.get('SERVER1','ip'))
        main_ser_port=int(config.get('SERVER1','port'))
        sub_ser_ip=str(config.get('SERVER2','ip'))
        sub_ser_port=int(config.get('SERVER2','port'))

        server_id = int(config.get('DEV_INFO','server_id'))
        dev_type = int(config.get('DEV_INFO','dev_type'))
        floor = int(config.get('DEV_INFO','floor'))

        f = open('/home/pi/fms/hangon/dev_type','r')

        for x in f:
                if x[0]=='#' or x[0]=='\n':
                        continue
                k, v, h = x.strip('\n').split(':')
                device_num[v]=int(k)
                device_info[v]=h
                #print (device_num)
                #print (device_info)

def connect():
        global sock
        global main_ser_ip
        global main_ser_port

        while 1:
                try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((main_ser_ip,main_ser_port))
                        break
                except:
                        time.sleep(1)
                        break

def connect_sub():
        global sock_sub
        global sub_ser_ip
        global sub_ser_port
        while 1:
                try:
                        sock_sub = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_sub.connect((sub_ser_ip,sub_ser_port))
                        break

                except:
                        time.sleep(1)
                        break

def socketClose():
        global sock
        global main_ser_ip
        global main_ser_port
        global sock_sub
        global sub_ser_ip
        global sub_ser_port

        try:
                sock.close()
                print("connection1 close")
        except:
                time.sleep(1)
        try:
                sock_sub.close()
                print("connection2 close")
        except:
                time.sleep(1)

def checksum(rev_data):
        data = rev_data[0:55]
        check_byte=rev_data[55:56]
        check_sum = int()
        #print (data)
        #print (check_byte)

        for x in data:
                check_sum += x

        if check_sum & 0xFF == int.from_bytes(check_byte, byteorder='big'):
                return True
        else:
                return False
        #print (check_sum & 0xFF)

def checksum_38(rev_data):
        data = rev_data[0:36]
        check_byte = rev_data[36:37]
        check_sum=int()

        for x in data:
                check_sum+= x

        if check_sum & 0xFF == int.from_bytes(check_byte, byteorder='big'):
                return Ture
        else:
                return False
#check checkxor
#input : read byte
#color monitor

"""
def checkxor(rev_data):
        data = rev_data[1:55]
        check_xor = int(rev_data[0:1])
        check_byte = rev_data[55:56]

        for x in  data:
                check_xor ^=x
        check_xor+=48

        if check_xor == ord(check_byte) :
                return True
        else:
                return False
"""
def checkxor(rev_data):
        try:
                data = rev_data[1:55]
                check_xor = int(rev_data[0:1])
                check_byte = rev_data[55:56]

                for x in  data:
                        check_xor ^=x
                check_xor+=48

                if check_xor == ord(check_byte) :
                        return True
                else:
                        return False

        except :
                #print ("int error")
                return False
def process_abnormal(dev_num):
        global sock
        global sock_sub
        global server_id
        global dev_type

        data = {"server_id":server_id, "dev_type":1, "dev_num":dev_num, "link":2,"floor":floor}
        return data

#process #4 ->d
def process_old(rev_data, dev_num) :

        global sock
        global sock_sub
        global server_id
        global dev_type
        global floor

        #rasp_id='1'

        if checksum(rev_data) == False:
                return False

        current_temperature = rev_data[0:3].decode('ascii')
        current_humidity = rev_data[3:6].decode('ascii')
        set_temp = rev_data[6:9].decode('ascii')
        #setting_humidity = rev_data[13:16].decode('ascii')
        set_high_temp = rev_data[22:25].decode('ascii')
        set_high_humi = rev_data[25:28].decode('ascii')

        #print  0==off    1==on
        #fms 1==off    2==on  so +1
        fan = int(rev_data[32:33].decode('ascii'))+1
        cs1 = int(rev_data[33:34].decode('ascii'))+1
        cs2 = int(rev_data[34:35].decode('ascii'))+1
        #warm_hit1 = int(rev_data[35:36].decode('ascii'))+1
        #warm_hit2 = int(rev_data[36:37].decode('ascii'))+1
        #warm_hit3 = int(rev_data[37:38].decode('ascii'))+1
        #warm_hit4 = int(rev_data[38:39].decode('ascii'))+1
        #warm_hit5 = int(rev_data[39:40].decode('ascii'))+1
        oper_humi = int(rev_data[40:41].decode('ascii'))+1
        oper_water = int(rev_data[41:42].decode('ascii'))+1
        oper_drain = int(rev_data[42:43].decode('ascii'))+1

        #ararm 0==off  1==on
        arm_high_tmp = int(rev_data[44:45].decode('ascii'))+1
        arm_comp1 = int(rev_data[45:46].decode('ascii'))+1
        arm_comp2 = int(rev_data[46:47].decode('ascii'))+1
        arm_heater= int(rev_data[47:48].decode('ascii'))+1
        arm_humidifier = int(rev_data[48:49].decode('ascii'))+1
        arm_fan = int(rev_data[49:50].decode('ascii'))+1
        arm_leak = int(rev_data[50:51].decode('ascii'))+1
        arm_temperature_senser = int(rev_data[51:52].decode('ascii'))+1
        arm_humidity_sensor = int(rev_data[52:53].decode('ascii'))+1

        #operate state
        operating_state = int(rev_data[54:55].decode('ascii'))
        if operating_state is 0:
                oper_stat = 1
        elif operating_state is 1:
                oper_stat =1
        else:
                oper_stat=2

        data = {"server_id":server_id,"dev_type":1,"dev_num":dev_num,"temp":current_temperature+"0",
                        "humi":current_humidity+"0","set_temp":set_temp+"0",
                        "set_high_humi":set_high_humi+"0", "set_high_temp":set_high_temp+"0","fan":fan,"cs1":cs1, 
                        "cs2":cs2,"oper_humi":oper_humi,"oper_water":oper_water,
                        "oper_drain":oper_drain, "arm_high_tmp":arm_high_tmp, "arm_comp1":arm_comp1, "arm_comp2":arm_comp2,
                        "arm_heater":arm_heater, "arm_humidifier":arm_humidifier, "arm_fan":arm_fan,
                        "arm_leak":arm_leak, "arm_temperature_senser":arm_temperature_senser, 
                        "arm_humidity_sensor":arm_humidity_sensor, "oper_stat":oper_stat, "link":1, "floor":floor }

        return data
        #print (data)
        #print ('tyep :'+data['type'])
        #print (type(data))
        #jdata = json.dumps(data)
        #print (jdata)
        #print (type(jdata))
        #sock.send(jdata.encode('utf-8'))
        data_en=json.dumps(data).encode('utf-8')
        datalen = len(data_en)
        datalen_b = struct.pack("!i",datalen)
        dataTosend = datalen_b + data_en
        #print (dataTosend)
        try:
                sock.send(dataTosend)
        except socket.error:
                connect()

        try:
                sock_sub.send(dataTosend)
        except socket.error:
                connect_sub()

        """
        print ('current_temperature: {}'.format(current_temperature))
        print ('current_humidity: {}'.format(current_humidity))
        print ('setting_temperature: {}'.format(setting_temperature))
        print ('setting_humidity: {}'.format(setting_humidity))
        print ('fan: {}'.format(fan))
        print ('cs1: {}'.format(cs1))
        print ('cs2: {}'.format(cs2))
        print ('worm_hit1: {}'.format(worm_hit1))
        print ('worm_hit2: {}'.format(worm_hit2))
        print ('worm_hit3: {}'.format(worm_hit3))
        print ('worm_hit4: {}'.format(worm_hit4))
        print ('worm_hit5: {}'.format(worm_hit5))
        print ('arm_high_tmp: {}'.format(arm_high_tmp))
        print ('arm_comp1: {}'.format(arm_comp1))
        print ('arm_comp2: {}'.format(arm_comp2))
        print ('arm_worm_hit: {}'.format(arm_worm_hit))
        print ('arm_humidification: {}'.format(arm_humidification))
        print ('arm_fan: {}'.format(arm_fan))
        print ('arm_leak: {}'.format(arm_leak))
        print ('arm_temperature_senser: {}'.format(arm_temperature_senser))
        print ('arm_humidity_sensor: {}'.format(arm_humidity_sensor))
        print ('operating_state: {}'.format(operating_state))
        """

def process_floor4(rev_data, dev_num) :

        global sock
        global sock_sub
        global server_id

        #rasp_id='1'

        if checksum(rev_data) == False:
                return False

        current_temperature = rev_data[0:3].decode('ascii')
        current_humidity = rev_data[3:6].decode('ascii')
        set_temp = rev_data[6:9].decode('ascii')
        #setting_humidity = rev_data[13:16].decode('ascii')
        set_high_temp = rev_data[22:25].decode('ascii')
        set_high_humi = rev_data[25:28].decode('ascii')

        #print  0==off    1==on
        #fms 1==off    2==on  so +1
        fan = int(rev_data[32:33].decode('ascii'))+1
        cs1 = int(rev_data[33:34].decode('ascii'))+1
        cs2 = int(rev_data[34:35].decode('ascii'))+1
        #warm_hit1 = int(rev_data[35:36].decode('ascii'))+1
        #warm_hit2 = int(rev_data[36:37].decode('ascii'))+1
        #warm_hit3 = int(rev_data[37:38].decode('ascii'))+1
        #warm_hit4 = int(rev_data[38:39].decode('ascii'))+1
        #warm_hit5 = int(rev_data[39:40].decode('ascii'))+1
        oper_humi = int(rev_data[40:41].decode('ascii'))+1
        oper_water = int(rev_data[41:42].decode('ascii'))+1
        oper_drain = int(rev_data[42:43].decode('ascii'))+1

        #ararm 0==off  1==on
        arm_high_tmp = int(rev_data[44:45].decode('ascii'))+1
        arm_comp1 = int(rev_data[45:46].decode('ascii'))+1
        arm_comp2 = int(rev_data[46:47].decode('ascii'))+1
        arm_heater= int(rev_data[47:48].decode('ascii'))+1
        arm_humidifier = int(rev_data[48:49].decode('ascii'))+1
        arm_fan = int(rev_data[49:50].decode('ascii'))+1
        arm_leak = int(rev_data[50:51].decode('ascii'))+1
        arm_temperature_senser = int(rev_data[51:52].decode('ascii'))+1
        arm_humidity_sensor = int(rev_data[52:53].decode('ascii'))+1

        #operate state
        operating_state = int(rev_data[54:55].decode('ascii'))
        if operating_state is 0:
                oper_stat = 1
        elif operating_state is 1:
                oper_stat =1
        else:
                oper_stat=2

        data = {"server_id":server_id,"dev_type":1,"dev_num":dev_num,"temp":current_temperature+"0","humi":current_humidity+"0",
                        "set_temp":set_temp+"0", "set_high_temp ":set_high_temp +"0",
                        "set_high_humi":set_high_temp +"0",
                        "fan":fan,"cs1":cs1, "cs2":cs2,"oper_humi":oper_humi, "oper_water":oper_water,
                        "oper_drain":oper_drain, "arm_high_tmp":arm_high_tmp, "arm_comp1":arm_comp1, "arm_comp2":arm_comp2,
                        "arm_heater":arm_heater, "arm_humidifier":arm_humidifier, "arm_fan":arm_fan,
                        "arm_leak":arm_leak, "arm_temperature_senser":arm_temperature_senser, 
                        "arm_humidity_sensor":arm_humidity_sensor, "oper_stat":oper_stat,"link":1, "floor":floor }
        #print (data)
        #print ('tyep :'+data['type'])
        #print (type(data))
        #jdata = json.dumps(data)
        #print (jdata)
        #print (type(jdata))
        #sock.send(jdata.encode('utf-8'))

        return data
        data_en=json.dumps(data).encode('utf-8')
        datalen = len(data_en)
        datalen_b = struct.pack("!i",datalen)
        dataTosend = datalen_b + data_en
        #print (dataTosend)
        """
        try:
                sock.send(dataTosend)
        except socket.error:
                connect()

        try:
                sock_sub.send(dataTosend)
        except socket.error:
                connect_sub()
        """

        """
        print ('current_temperature: {}'.format(current_temperature))
        print ('current_humidity: {}'.format(current_humidity))
        print ('setting_temperature: {}'.format(setting_temperature))
        print ('setting_humidity: {}'.format(setting_humidity))
        print ('fan: {}'.format(fan))
        print ('cs1: {}'.format(cs1))
        print ('cs2: {}'.format(cs2))
        print ('worm_hit1: {}'.format(worm_hit1))
        print ('worm_hit2: {}'.format(worm_hit2))
        print ('worm_hit3: {}'.format(worm_hit3))
        print ('worm_hit4: {}'.format(worm_hit4))
        print ('worm_hit5: {}'.format(worm_hit5))
        print ('arm_high_tmp: {}'.format(arm_high_tmp))
        print ('arm_comp1: {}'.format(arm_comp1))
        print ('arm_comp2: {}'.format(arm_comp2))
        print ('arm_worm_hit: {}'.format(arm_worm_hit))
        print ('arm_humidification: {}'.format(arm_humidification))
        print ('arm_fan: {}'.format(arm_fan))
        print ('arm_leak: {}'.format(arm_leak))
        print ('arm_temperature_senser: {}'.format(arm_temperature_senser))
        print ('arm_humidity_sensor: {}'.format(arm_humidity_sensor))
        print ('operating_state: {}'.format(operating_state))
        """



def process_color(rev_data, dev_num) :

        global sock
        global sock_sub
        global rasp_id

        if checkxor(rev_data) == False:
                return False

        current_temperature = rev_data[0:3].decode('ascii')
        current_humidity = rev_data[3:6].decode('ascii')
        set_temp = rev_data[6:9].decode('ascii')
        set_high_temp = rev_data[22:25].decode('ascii')
        set_high_humi = rev_data[25:28].decode('ascii')

        #setting_humidity = rev_data[13:16].decode('ascii')

        #0== off  1==on
        #fms 1==off 2==on so +1
        fan = int(rev_data[32:33].decode('ascii'))+1
        cs1 = int(rev_data[33:34].decode('ascii'))+1
        cs2 = int(rev_data[34:35].decode('ascii'))+1
        #warm_hit1 = int(rev_data[35:36].decode('ascii'))+1
        #warm_hit2 = int(rev_data[36:37].decode('ascii'))+1
        #warm_hit3 = int(rev_data[37:38].decode('ascii'))+1
        #warm_hit4 = int(rev_data[38:39].decode('ascii'))+1
        #warm_hit5 = int(rev_data[39:40].decode('ascii'))+1
        oper_humi = int(rev_data[40:41].decode('ascii'))+1
        #not exist oper_drain

        arm_high_tmp = int(rev_data[44:45].decode('ascii'))+1
        arm_comp1 = int(rev_data[45:46].decode('ascii'))+1
        arm_comp2 = int(rev_data[46:47].decode('ascii'))+1
        arm_heater= int(rev_data[47:48].decode('ascii'))+1
        arm_humidifier = int(rev_data[48:49].decode('ascii'))+1
        arm_fan = int(rev_data[49:50].decode('ascii'))+1
        arm_leak = int(rev_data[50:51].decode('ascii'))+1
        arm_temperature_senser = int(rev_data[51:52].decode('ascii'))+1
        arm_humidity_sensor = int(rev_data[52:53].decode('ascii'))+1

        #2==operating    1==stop
        operating_state = int(rev_data[54:55].decode('ascii'))
        oper_stat = operating_state

        data={"server_id":server_id,"dev_type":1,"dev_num":dev_num,"temp":current_temperature+"0",
                "humi":current_humidity+"0","set_temp":set_temp+"0",
                "set_high_temp":set_high_temp+"0","set_high_humi":set_high_humi+"0",
                "fan":fan,"cs1":cs1, "cs2":cs2,"oper_humi":oper_humi,
                "arm_high_tmp":arm_high_tmp, "arm_comp1":arm_comp1, "arm_comp2":arm_comp2,
                "arm_heater":arm_heater, "arm_humidifier":arm_humidifier, "arm_fan":arm_fan,
                "arm_leak":arm_leak, "arm_temperature_senser":arm_temperature_senser,
                "arm_humidity_sensor":arm_humidity_sensor, "oper_stat":oper_stat, "link":1, "floor":floor }

        #print (data)
        return data

        dataTosend = json.dumps(data).encode('utf-8')




def process_38(rev_data, dev_num) :
        global sock
        global sock_sub
        global rasp_id

        current_temperature = rev_data[0:3].decode('ascii')
        current_humidity = rev_data[3:6].decode('ascii')

        alarm1_byte = rev_data[22:23] #operating _state
        alarm1_int = int.from_bytes(alarm1_byte,'big')
        if alarm1_int & 1 ==0:
                pass
        else :
                pass
        if alarm1_int & 2 ==0:
                pass
        else :
                pass
        if alarm1_int & 4 ==0:
                pass
        else :
                pass
        if alarm1_int & 8 ==0:
                alarm = 1
        else:
                alarm = 2

        if alarm1_int & 16 ==0:
                oper_dehumi = 1
        else:
                oper_dehumi = 2

        if alarm1_int & 32 ==0:
                oper_humi = 1
        else:
                oper_humi = 2

        if alarm1_int & 64 ==0:
                oper_warm = 1
        else :
                oper_warm = 2

        if alarm1_int & 128 ==0:
                oper_cool = 1
        else:
                oper_cool = 2


        alarm2_byte = rev_data[23:24] #print _state 1
        alarm2_int = int.from_bytes(alarm2_byte,'big')
        if alarm2_int & 1 ==0:
                warm_hit3 = 1
        else:
                warm_hit3 = 2

        if alarm2_int & 2 == 0:
                warm_hit2 = 1
        else :
                warm_hit2 = 2

        if alarm2_int & 4 ==0:
                warm_hit1 = 1
        else :
                warm_hit1 = 2

        if alarm2_int & 8 ==0:
                comp2_mg = 1
        else:
                comp2_mg = 2

        if alarm2_int & 16 ==0 :
                comp2_sol = 1
        else :
                comp2_sol = 2

        if alarm2_int & 32 ==0 :
                comp1_mg = 1
        else:
                comp1_mg = 2

        if alarm2_int & 64 == 0:
                comp1_sol = 1
        else :
                comp1_sol = 2

        if alarm2_int & 128 == 0:
                fan = 1
        else : 
                fan = 2

        alarm3_byte = rev_data[24:25] #print state 2
        alarm3_int = int.from_bytes(alarm3_byte,'big')
        #if alarm3_int & 1 ==0:

        if alarm3_int & 2 ==0:
                drain = 1
        else:
                drain = 2

        #alarm3_int & 4 ==0:

        if alarm3_int & 8 ==0:
                water_supply = 1
        else :
                water_supply = 2

        if alarm3_int & 16 ==0:
                humi_hit2 = 1
        else :
                humi_hit2 = 2

        if alarm3_int & 32 ==0:
                humi_hit1 = 1
        else:
                humi_hit1 = 2

        if alarm3_int & 64 ==0:
                warm_hit5 = 1
        else :
                warm_hit5 = 2

        if alarm3_int & 128 ==0:
                warm_hit4 = 1
        else :
                warm_hit4 = 2

        alarm4_byte = rev_data[26:27] #alarm state1
        alarm4_int = int.from_bytes(alarm4_byte,'big')
        if alarm4_int & 1 == 0 :
                arm_humi_hit = 1
        else :
                arm_humi_hit = 2

        if alarm4_int & 2 == 0:
                arm_hit = 1
        else:
                arm_hit = 2

        if alarm4_int & 4 == 0:
                arm_comp2 = 1
        else :
                arm_comp2 = 2

        if alarm4_int & 8 == 0:
                arm_comp1 = 1
        else :
                arm_comp1 = 2

        #if alarm4_int & 16
        #if alarm4_int & 32
        if alarm4_int & 64 == 0:
                arm_high_temp=1
        else:
                arm_high_temp=2

        #if alarm4_int & 128

        alarm5_byte = rev_data[27:28] #alarm state2
        alarm5_int = int.from_bytes(alarm5_byte,'big')
        #if alarm5_int & 1 == 0 :
        #if alarm5_int & 2 == 0 :
        #if alarm5_int & 4 == 0 :
        if alarm5_int & 8 == 0 :
                arm_high_humi = 1
        else:
                arm_high_humi = 2

        if alarm5_int & 16 == 0 :
                arm_humi_sensor =1
        else:
                arm_humi_sensor =2

        if alarm5_int & 32 == 0 :
                arm_temp_sensor = 1
        else:
                arm_temp_sensor = 2

        if alarm5_int & 64 == 0 :
                arm_leak = 1
        else:
                arm_leak = 2

        if alarm5_int & 128 == 0 :
                arm_fan = 1
        else:
                arm_fan = 2

        oper_state = rev_data[35:36].decode('ascii')
         


def send_data(data):
        global sock
        global sock_sub
        print(type(data))
        data_en=json.dumps(data).encode('utf-8')
        datalen = len(data_en)
        datalen_b = struct.pack("!i",datalen)
        dataTosend = datalen_b + data_en

        print(str(dataTosend))

        try:
                sock.send(dataTosend)
                print("11111111111")
        except Exception as e:
                print(e)
                connect()

        try:
                sock_sub.send(dataTosend)
                print("222222222222")
        except Exception as e:
                print(e)
                connect_sub()


def processing():
        #postfix = b'?0'  #black and white monitor
        postfix = b'??'   #color monitor
        port = "/dev/ttyUSB0"
        baud = 9600
        while(1):
            ser = serial.Serial(port,baud,timeout=0.5)
            if ser.isOpen():
                print(ser.name + 'is open...')
            for dev_id in device_info:
                    time.sleep(1)
                    if device_info.get(dev_id) == 'color_AAA':
                            try:
                                f = open('/home/pi/fms/hangon/test/color_AAA','r')
                                data = f.readline()
                                send_data(dict(data))
                                continue
                            except:
                                print("color_AAA no data")
                                continue

                    else:
                        command = dev_id.encode('ascii') + postfix
                        print (command)
                        check_count = 0
                        while True:
                                ser.write(command)
                                rev_data = ser.readline()

                                #time.sleep(5)
                                #ser.write(command)
                                #rev_data2= ser.readline()

                                #print (command)
                                #print(rev_data)
                                #print(rev_data2)
                                print(" ")

                                if check_count>=10:
                                        rev_data=b''
                                        break
                                if len(rev_data)!=56:
                                        check_count=check_count+1
                                        #print("not 56")
                                        continue
                                else:
                                        break


                                """if len(rev_data)!=56 or len(rev_data2)!=56:
                                        print ('len !56')
                                        print (rev_data)
                                        print (rev_data2)
                                        check_count=check_count+1
                                        continue

                                #if rev_data == rev_data2:
                                if rev_data[6:55] == rev_data2[6:55]:
                                        #print ('send')
                                        #print (command)
                                        #print (rev_data)
                                        break
                                else:
                                        print ('else')
                                        print (command)
                                        print (rev_data)
                                        print (rev_data2)
                                        check_count=check_count+1"""


                        #print(command)
                        #print(rev_data)
                        if rev_data == b'' or len(rev_data)!=56:
                                print ('abnormal')
                                print (command)
                                print (rev_data)
                                data = process_abnormal(device_num.get(dev_id))
                                send_data(data)
                                print (data)
                                continue
                        else :
                                pass
                                #print (rev_data)

                        #continue

                        if device_info.get(dev_id) == 'old' :
                                data = process_old(rev_data, device_num.get(dev_id))
                                if data == False:
                                        print ('false')
                                else:
                                        send_data(data)

                        elif device_info.get(dev_id)=='color':
                                data = process_color(rev_data, device_num.get(dev_id))
                                if data == False:
                                        print ('false')
                                else:
                                        #print (data)
                                        send_data(data)

                        elif device_info.get(dev_id)=='old_4':
                                data = process_floor4(rev_data, device_num.get(dev_id))
                                if data == False:
                                        print ('false')
                                else:
                                        send_data(data)
                        else:
                                print ('false : {}'.format(command))
                        time.sleep(2)
            ser.close()
            print("ser.close()")
            os.system('python hangon2.py &')
            time.sleep(2)

def main():
        connect()
        connect_sub()
        init()
        processing()
        socketClose()

if __name__=='__main__':
        main()