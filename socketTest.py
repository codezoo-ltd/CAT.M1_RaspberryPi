from CZCATM1.CATM1 import CATM1
import time 
import RPi.GPIO as GPIO

node = CATM1()

#Wait for the LTE Network to connect
time.sleep(2)
while True:
    if node.isAttachNetwork():
        print("Network connect")
        break
    else:
        print("Network disconnect")

print("Activate PDP Context: " + node.attachNetwork())
print("myIP: " + node.myIP())

#UDP Socket Test
socketNum = 0
if node.openSocket(socketNum, 0, "\"echo.mbedcloudtesting.com\"", 7):
    print("UDP Socket Open")
else:
    print("UDP Socket Open Error")	

node.sendSCKData(socketNum, "Hello World")
print(">>> UDP Test Result : " + node.receiveSCKData(socketNum))
if node.closeSocket(socketNum):
    print("UDP Socket Close")
else:
    print("UDP Socket Close Error")	

#TCP Socket Test
if node.openSocket(socketNum, 1, "\"echo.mbedcloudtesting.com\"", 7):
    print("TCP Socket Open")
else:
    print("TCP Socket Open Error")	

node.sendSCKData(socketNum, "Hello World")
print(">>> TCP Test Result : " + node.receiveSCKData(socketNum))
if node.closeSocket(socketNum):
    print("TCP Socket Close")
else:
    print("TCP Socket Close Error")	

#Deactiveate Network
print("Deactivate PDP Context: " + node.attachNetwork(False))
time.sleep(2)

#program End
GPIO.cleanup()
