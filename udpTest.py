from CZCATM1.CATM1 import CATM1
import time 
import RPi.GPIO as GPIO

server_ip = "52.215.34.155"
server_port = 7


node = CATM1()

#print("reset start")
#node.resetModem()
#print("reset end")

print("AT: " + node.sendATCmd("AT", "OK\r\n"))
print("IMEI: " + node.getIMEI()) 
print("FW Ver: " + node.getFirmwareInfo())
print("HW model: " + node.getHardwareInfo())

if node.isAttachNetwork():
    print("Network connect")
else:
    print("Network disconnect")
    node.attachNetwork()

#node.closeUDPSocket(0)
socket = node.openUDPSockect()

node.setPortNum(server_port)
node.setIPAddress(server_ip)
node.sendUDPData(socket, "Hi There")
print(node.receiveUDPData(socket))

node.closeUDPSocket(socket)
