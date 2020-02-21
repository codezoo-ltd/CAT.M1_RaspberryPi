from CZCATM1.CATM1 import CATM1
import time 
import RPi.GPIO as GPIO

node = CATM1()

#node.resetModem()

print("AT: " + node.sendATCmd("AT", "OK\r\n"))
print("ATE0: " + node.sendATCmd("ATE0", "OK\r\n"))
print("IMEI: " + node.getIMEI()) 
print("FW Ver: " + node.getFirmwareInfo())
print("HW model: " + node.getHardwareInfo())
print("Phone Number: " + node.getPhoneNumberInfo())
time.sleep(2)
#print("Network Register: " + node.isAttachNetwork())
if node.isAttachNetwork():
	print("Network connect")
else:
	print("Network disconnect")

#program End
GPIO.cleanup()
