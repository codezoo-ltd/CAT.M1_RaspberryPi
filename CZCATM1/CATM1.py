import time
import serial
import re
import threading
import RPi.GPIO as GPIO

ATCmdList = {
    'IMEI': {'CMD': "AT+CGSN", 'REV': "\r\nOK\r\n"},
    'FWInfo': {'CMD': "AT+CGMR", 'REV': "\r\nOK\r\n"},
    'HWInfo': {'CMD': "AT+CGMM", 'REV': "\r\nOK\r\n"},
    'NumberInfo': {'CMD': "AT+CIMI", 'REV': "\r\nOK\r\n"},
    'AttachNet' : {'CMD': "AT+CGATT=1", 'REV': "OK\r\n"},
    'DetachNet' : {'CMD': "AT+CGATT=0", 'REV': "OK\r\n"},
    'IsAttachNet' : {'CMD': "AT+CEREG?", 'REV': "+CEREG: \r\n"},
#    'IsAttachNet' : {'CMD': "AT+CEREG?", 'REV': "\r\nOK\r\n"},
    'OpenUDP' : {'CMD': "AT+NSOCR=DGRAM,17,", 'REV': "OK\r\n"},
    'CloseUDP' : {'CMD': "AT+NSOCL=", 'REV': "\r\n"}, 
    'SendUDP' : {'CMD': "AT+NSOST=", 'REV': "\r\n"},
    'RecevieUDP' : {'CMD': "AT+NSORF=", 'REV': "OK\r\n"},
}

IsRevModemData = False

class CATM1:
    ser = None
    isConectSerial = False
    __TimeOut = 5     # seconds

    def __init__(self, serialPort='/dev/ttyS0', baudrate=115200, pwrPinNum=17, statPinNum=27):

        # serial port setup
        if(CATM1.isConectSerial == False):
            CATM1.ser = serial.Serial()
            CATM1.ser.port = serialPort
            CATM1.ser.baudrate = baudrate
            CATM1.ser.parity = serial.PARITY_NONE
            CATM1.ser.stopbits = serial.STOPBITS_ONE
            CATM1.ser.bytesize = serial.EIGHTBITS
            CATM1.isConectSerial = True

        # Modem Power setup
        self.pwrPinNum = pwrPinNum
        self.statPinNum = statPinNum
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwrPinNum, GPIO.OUT)
        GPIO.setup(self.statPinNum, GPIO.IN)

		# Check Modem Power State Check
        if(GPIO.input(self.statPinNum)==1):
			print "Modem Power ON State Reset Modem"
			GPIO.output(self.pwrPinNum, GPIO.HIGH)
			time.sleep(0.8)
			GPIO.output(self.pwrPinNum, GPIO.LOW)
			time.sleep(3)

		# Modem Power ON
        GPIO.output(self.pwrPinNum, GPIO.HIGH)
        time.sleep(0.6)
        GPIO.output(self.pwrPinNum, GPIO.LOW)
        time.sleep(5)
        if(GPIO.input(self.statPinNum) == 1):
			print "Modem Power ON State Start Modem"

        self.compose = ""
        self.response = ""
        self.timeout = CATM1.__TimeOut

        self.ipAddress = ""
        self.portNum = ""

    def getPwrPinNum(self):
        ''' get modem Power pin number '''
        return self.pwrPinNum
    
    def getStatusPinNum(self):
        ''' get modem Status pin number '''
        return self.statPinNum

    def pwrOnModem(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwrPinNum, GPIO.OUT)
        GPIO.output(self.pwrPinNum, GPIO.HIGH)
        time.sleep(0.6)
        GPIO.output(self.pwrPinNum, GPIO.LOW)
        time.sleep(5)

    def pwrOffModem(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwrPinNum, GPIO.OUT)
        GPIO.output(self.pwrPinNum, GPIO.HIGH)
        time.sleep(0.8)
        GPIO.output(self.pwrPinNum, GPIO.LOW)
        time.sleep(3)

    def resetModem(self):
		self.pwrOffModem()
		self.pwrOnModem()

    def setIPAddress(self, ip):
        ''' set ip address'''
        self.ipAddress = ip
    
    def setPortNum(self, port):
        ''' set port number '''
        self.portNum = str(port)

    def __getMillSec(self):
        ''' get miliseconds '''
        return int(time.time())
    
    def __delay(self, ms):
        ''' delay as millseconds '''
        time.sleep(float(ms/1000.0))

    def __readATResponse(self, cmd_response):
        ''' getting respnse of AT command from modem '''
        timer = self.__getMillSec()
        timeout = self.timeout
        response = self.response

        while True:
            self.response = ""
            while(CATM1.ser.inWaiting()):
                try:
                    self.response += CATM1.ser.read(CATM1.ser.inWaiting()).decode('utf-8', errors='ignore')
                    print("read response: " + self.response)
                    response = self.response
                    self.__delay(50)
                except Exception as e:
                    print(e)
                    return False
            if(self.response.find(cmd_response) != -1):
                #print("read response: " + self.response)
                return True
            if((self.__getMillSec() - timer) > timeout):
                # error rasie
                print("Recv failed: " + response)
                return False

    def __sendATCmd(self, command):
        ''' Sending at AT command to module '''
        self.compose = ""
        self.compose = str(command) + "\r"
        CATM1.ser.reset_input_buffer()
        CATM1.ser.write(self.compose.encode())
        #print(self.compose)
    
    def sendATCmd(self, command, cmd_response, timeout = None):
        ''' Send AT command & Read command response ''' 
        if(CATM1.ser.isOpen() == False):
            CATM1.ser.open()

        if timeout is None:
            timeout = self.timeout
        
        self.__sendATCmd(command)

        timer = self.__getMillSec()

        while True: 
            if((self.__getMillSec() - timer) > timeout):
                # error rasie
                print(command + " / Send failed ")
                return "Error"
            
            if(self.__readATResponse(cmd_response)):
                return self.response

    # AT command methods
    def getIMEI(self):
        ''' get IMEI number'''
        data = self.sendATCmd(ATCmdList['IMEI']['CMD'], ATCmdList['IMEI']['REV'])
        return data[:data.index(ATCmdList['IMEI']['REV'])]

    def getFirmwareInfo(self):
        ''' get FW version '''
        data =  self.sendATCmd(ATCmdList['FWInfo']['CMD'], ATCmdList['FWInfo']['REV'])
        return data[:data.index(ATCmdList['FWInfo']['REV'])]

    def getHardwareInfo(self):
        ''' get modem model info '''
        data = self.sendATCmd(ATCmdList['HWInfo']['CMD'], ATCmdList['HWInfo']['REV'])
        return data[:data.index(ATCmdList['HWInfo']['REV'])]

    def getPhoneNumberInfo(self):
        ''' get modem phone number '''
        data = self.sendATCmd(ATCmdList['NumberInfo']['CMD'], ATCmdList['NumberInfo']['REV'])
        return data[:data.index(ATCmdList['NumberInfo']['REV'])]
 
    def attachNetwork(self, connect=True):
        ''' connect/disconnect base station fo operator '''
        if(connect):
            return self.sendATCmd(ATCmdList['AttachNet']['CMD'], ATCmdList['AttachNet']['REV'], 8)
        else:
            return self.sendATCmd(ATCmdList['DetachNet']['CMD'], ATCmdList['DetachNet']['REV'], 8)
    
    def isAttachNetwork(self):
        ''' true : LTE CAT.M1 Network attached, false : LTE CAT.M1 Network detached ''' 
        return (self.sendATCmd(ATCmdList['IsAttachNet']['CMD'], ATCmdList['IsAttachNet']['REV']) != "Error")
#        data = self.sendATCmd(ATCmdList['IsAttachNet']['CMD'], ATCmdList['IsAttachNet']['REV'])
#        return data[:data.index(ATCmdList['IsAttachNet']['REV'])]

    # UDP methods 
    def openUDPSockect(self, port=10):
        ''' port = 0~65535 (reserve 5683) '''
        command = ATCmdList['OpenUDP']['CMD'] + str(port) + ',1'
        mySocket = self.sendATCmd(command, ATCmdList['OpenUDP']['REV'])

        if(mySocket != "Error"):
            return int(re.search(r'\d+', mySocket).group())
        else:
            return -1
    
    def closeUDPSocket(self, mySocket):
        command = ATCmdList['CloseUDP']['CMD'] + str(mySocket)
        self.sendATCmd(command, ATCmdList['CloseUDP']['REV'])
        
    # data type
    def sendUDPData(self, mySocket, data, ip_address=None, ip_port=None):
        ''' send UDP data 
            max data size: 256bytes -> recomand 250bytes 
            send data is Nibble type (ex, "A" -> 0x41)'''
        command = ATCmdList['SendUDP']['CMD'] + str(mySocket) + ","
        if ip_address is None:
            command += self.ipAddress
        else:
            command += str(ip_address)
        command += ","
        if ip_port is None:
            command += self.portNum
        else:
            command += str(ip_port)
        command += ","
        command += str(len(data)) + "," + data.encode().hex()

        self.sendATCmd(command, ATCmdList['SendUDP']['REV'], 10)

    def __revModem_Thread(self):
        if self.__readATResponse("+NSONMI"):
            global IsRevModemData
            IsRevModemData  = True

    def recevieUDPData(self, mySocket, rev_length=256, rev_timeOut=10):
        ''' recevie buffer size : 512 bytes 
        return : ['ip','port','data length', 'data', 'renainnig length']'''
        duration = 500
        count = ((rev_timeOut*1000)/duration)
        datareceve = False
        data_length = ""

        global IsRevModemData
        IsRevModemData  = False 
        t1 = threading.Thread(target=self.__revModem_Thread)
        t1.daemon = True
        t1.start()
        for i in range(0,int(count)):
            if IsRevModemData:
                datareceve = True
                data = self.response.split(',')
                data_length = data[len(data)-1]
                break
            else:
                #print("wait index {}".format(i))
                self.__delay(duration)

        if datareceve == False:
            try:
                t1._stop()
                del t1
            except AssertionError as e:
                print(e)
            
        if(datareceve):
            if int(data_length) > rev_length :
                data_length = str(rev_length)
            command = ATCmdList['RecevieUDP']['CMD'] + str(mySocket) + "," + data_length
            if (self.sendATCmd(command, ATCmdList['RecevieUDP']['REV']) != "Error"):
               data = self.response.split(',')
               data[4] = bytes.fromhex(data[4]).decode('utf-8')
               data[5] = re.search(r'\d+', data[5]).group()
               return data[1:]

        print("Data read fail")
        return ['-1','-1','-1','-1','-1']
