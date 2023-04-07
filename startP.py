#!/usr/bin/env python
import os
import sys
import time

def main():
        time.sleep(1)
        while 1:
                oscommand = os.popen('ps -ef | grep -v "grep" | grep "hangon.py" | wc -l ').readlines()
                check_process = "%s" % (oscommand[0])
                if int(check_process) == 0 :
                        os.system("python3 /home/pi/fms/hangon/hangon.py &")
                try:
                        time.sleep(8)

                except Exception, e:
                        print e
                        sys.exit()
if __name__ == "__main__":
        main()