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
    'AttachNet' : {'CMD': "AT+QIACT=1", 'REV': "\r\nOK\r\n"},
    'myIP' : {'CMD': "AT+QIACT?", 'REV': "\r\nOK\r\n"},
    'DetachNet' : {'CMD': "AT+QIDEACT=1", 'REV': "\r\nOK\r\n"},
    'IsAttachNet' : {'CMD': "AT+CEREG?", 'REV': "\r\nOK\r\n"},
    'OpenSCK' : {'CMD': "AT+QIOPEN=1,", 'REV': "\r\n+QIOPEN"},
    'CloseSCK' : {'CMD': "AT+QICLOSE=", 'REV': "\r\nOK\r\n"}, 
    'SendSCK' : {'CMD': "AT+QISENDEX=", 'REV': "\r\nSEND OK"},
    'ReceiveSCK' : {'CMD': "AT+QIRD=", 'REV': "\r\nOK\r\n"},
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

		# Modem Power Power On Reset
        if(GPIO.input(self.statPinNum)==1):
			print("Reset Modem..")
			self.pwrOffModem()

        print "Start Modem.."
        self.pwrOnModem()
        if(GPIO.input(self.statPinNum) == 1):
			print("Modem Ready..")
        else:
			print("Modem Not Ready..")

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
    
    def setDNSAddress(self, dns):
        ''' set ip address'''
        self.ipAddress = dns

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
                    #print("read response: " + self.response)
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
        ''' Activate/Deactivate a PDP Context '''
        if(connect):
            return self.sendATCmd(ATCmdList['AttachNet']['CMD'], ATCmdList['AttachNet']['REV'], 10)
        else:
            return self.sendATCmd(ATCmdList['DetachNet']['CMD'], ATCmdList['DetachNet']['REV'], 10)
    
    def isAttachNetwork(self):
        ''' True : LTE CAT.M1 Network attached, False : LTE CAT.M1 Network detached ''' 
        data = self.sendATCmd(ATCmdList['IsAttachNet']['CMD'], ATCmdList['IsAttachNet']['REV'])
        _str = ',1'
        if(data.find(_str)==-1):
            return False
        else:
            return True

    def myIP(self):
        ''' get modem IP Address '''
        data = self.sendATCmd(ATCmdList['myIP']['CMD'], ATCmdList['myIP']['REV'], 10)
        _str = ',"'
        _len = len(data)-7

        idx = data.find(_str)
        if(idx == -1):
            return False
        else:
            return data[idx+1:_len]
 
    # Socket methods 
    def openSocket(self, mySocket, isTCP, ip_address=None, ip_port=None):
        if (isTCP == True):
            command = ATCmdList['OpenSCK']['CMD'] + str(mySocket) + ',"TCP",'
        else:
            command = ATCmdList['OpenSCK']['CMD'] + str(mySocket) + ',"UDP",'

        if ip_address is None:
            command += self.ipAddress
        else:
            command += str(ip_address)

        command += ','
        if ip_port is None:
            command += self.portNum
        else:
            command += str(ip_port)
        command += ',0,0'	#Buffer access mode 

        #print(command)

        data = self.sendATCmd(command, ATCmdList['OpenSCK']['REV'], 10)

        if( data  == "Error" ):
            return False
        else:
            return True
    
    def closeSocket(self, mySocket):
        command = ATCmdList['CloseSCK']['CMD'] + str(mySocket)
        command += ',3'	#TimeOut Default 10 to 3 seconds
        data = self.sendATCmd(command, ATCmdList['CloseSCK']['REV'], 10)
        if( data  == "Error" ):
            return False
        else:
            return True
        
    # data type
    def sendSCKData(self, mySocket, data):
        ''' send UDP data 
            max data size: 512 bytes (Hex string) '''
        command = ATCmdList['SendSCK']['CMD'] + str(mySocket) + ","
        command += '"'
        command += data.encode("hex")
        command += '"'

        result = self.sendATCmd(command, ATCmdList['SendSCK']['REV'], 10)

        if( result == "Error" ):
			return False
        else:
		    return True

    def __revModem_Thread(self):
        if self.__readATResponse('+QIURC: "recv"'):
            global IsRevModemData
            IsRevModemData  = True

    def receiveSCKData(self, mySocket, rev_length=256, rev_timeOut=10):
        ''' recevie buffer size : 1460 bytes 
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
            command = ATCmdList['ReceiveSCK']['CMD'] + str(mySocket)
            if (self.sendATCmd(command, ATCmdList['ReceiveSCK']['REV']) != "Error"):
               data = self.response.split('\n')

               result = data[2]
               result2 = result[:-1]
               length = len(result2)
               #print( str(length) )
		       	   
               return result2

        print("Data read fail")
        return ['-1','-1','-1','-1','-1']
