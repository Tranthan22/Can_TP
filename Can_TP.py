import can
import copy
import time
import threading
from typing import List
from PDUs import PDU_App_T, PDU_App_R
from Common import I_PDU, N_PDU, FS_t, Connection_Stage
from Can_LL import Bus
 
 
""" ===========================================================================================
Module              : Can_TP
Brief               : Main module for Can-TP
=========================================================================================== """
class Can_TP_Config:
    def __init__(self, BS = 5, STmin = 0.01):
        self.BS = BS
        self.STmin = STmin
 
class Can_TP_Connection:
    def __init__(self, connectionID):
        self.TP_Config = Can_TP_Config()
        self.connectionID = connectionID
        self.transmiting = False
        self.receiving = False
        self.sequence = 0
        self.index = 0
        self.sequenceIdx = 0
        self.expected_length = 0        # Length of message (include data in  FF and CF)
        self.stage : Connection_Stage = Connection_Stage.UNKNOW_STATE
 
class Can_TP:
    ''' Constructor '''
    def __init__(self):
        self.LL_bus = Bus()
        self.connections_T : List[Can_TP_Connection] = []
        self.connections_R : List[Can_TP_Connection] = []
        self.TP_transmit = TP_Transmit(self.LL_bus, self.connections_T)
        self.TP_receive = TP_Receive(self.connections_R)
        self.main_thread = None
 
    ''' Destructor '''
    def __del__(self):
        print("Destructor: CanTP")
 
    def init(self):
        # Init Can LL
        self.LL_bus.init()
        self.main_thread = threading.Thread(target=self.TP_transmit.Main_Fuction)
        self.main_thread.daemon = True
        self.main_thread.start()
 
    # Register handle and enable listening
    def startListen(self):
        self.LL_bus.startListen(self.TP_receive)
   
    # Create sending request
    def transmitMessage(self, I_PDU : I_PDU):
        self.TP_transmit.transmit(I_PDU)
 
 
 
""" ===========================================================================================
Module              : TP_Transmit
Brief               : Module provides method for handling transmiting operation
                    of Can-TP layer
============================================================================================"""
class TP_Transmit:
    ''' Constructor '''
    def __init__(self, bus : Bus, connections_T : List[Can_TP_Connection]):
        # print("Constructor: CanTP Transmit")
        self.bus = bus
        self.connections_T = connections_T
 
    ''' Destructor '''
    def __del__(self):
        # print("Destructor: CanTP Transmit")
        pass
   
    """ Create request to send """
    def transmit(self, I_PDU : I_PDU):
        self.connections_T.append( Can_TP_Connection(I_PDU.ID))
       
    """ Transmit mainfunction periodically works """
    def Main_Fuction(self):
        global PDU_App_T
        while 1:
            connectionsAtTime = copy.deepcopy(self.connections_T)
            # Operate with every connection
            for connection in connectionsAtTime:
                # Finding the PDU which the connection works with
                for pdu in PDU_App_T:
                    if connection.connectionID == pdu.ID:
                        # Send SF
                        if pdu.SDULength() <= 7 or (pdu.SDULength() <= 62 and pdu.is_FD == True):
                            self.transmitSF(pdu)
 
                        # Send Segmentation
                        else:
                            self.transmitFF(pdu, connection)
                            while connection.transmiting is True:
                                # if connection.stage != Connection_Stage.SENDING_CF_CONTINOUS:
                                self.transmitCF(pdu, connection)
                                    # time.sleep(connection.TP_Config.STmin)
                        break
           
            # Remove refesh requests
            if len(connectionsAtTime) == len(self.connections_T):
                self.connections_T.clear()
            else:
                for i in range(len(connectionsAtTime)):
                    # Remove some completed request
                    if connectionsAtTime[i] != self.connections_T[i]:
                        self.connections_T = self.connections_T[i:]
            time.sleep(2)
           
    # Send SINGLE FRAME
    def transmitSF(self, I_PDU : I_PDU):
        SDULength = I_PDU.SDULength()
        N_PDU = copy.deepcopy(I_PDU)
        N_SDU = I_PDU.SDU
 
        if(I_PDU.is_FD is not True):
            N_PCI = [(0 | SDULength & 0x0F)]       # Classic CAN
        else:
            N_PCI = [0 , SDULength]         # Can FD
 
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
 
    # Send FIRST FRAME
    def transmitFF(self, I_PDU : I_PDU, connection : Can_TP_Connection):
        SDULength = I_PDU.SDULength()
        N_PDU = copy.deepcopy(I_PDU)
 
        if(I_PDU.is_FD is not True):
            # Classical Can
            N_PCI = [(0x01 << 4 | (SDULength >> 8)), (SDULength & 0xFF)]
            N_SDU = I_PDU.SDU[:6]
            connection.index = 13
        else:
            # Can FD
            N_PCI = [(0x01 << 4), 0x00, (SDULength >> 24 & 0xFF),(SDULength >> 16 & 0xFF), (SDULength >> 8 & 0xFF), (SDULength & 0xFF)]
            N_SDU = I_PDU.SDU[:58]              # 64 - 6 PCI bytes
            connection.index = 121
       
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.stage = Connection_Stage.SENT_FF
        connection.transmiting = True
       
    # Send CONSECUTIVE FRAME
    def transmitCF(self, I_PDU : I_PDU, connection : Can_TP_Connection):
        N_PDU = copy.deepcopy(I_PDU)
 
        connection.sequence += 1
        if connection.sequence >= 16:
            connection.sequence = 0
 
        N_PCI = [0x02 << 4 | (connection.sequence & 0x0F)]
 
        if(I_PDU.is_FD is not True):
            # Classical Can
            N_SDU = I_PDU.SDU[connection.index - 7 : connection.index]
            connection.index += 7
            # Completely send
            if connection.index > I_PDU.SDULength() + 7:
                connection.transmiting = False
                connection.sequence = 0
                connection.index = 0
        else:
            # Can FD
            N_SDU = I_PDU.SDU[connection.index - 63 : connection.index]
            connection.index += 63
            # Completely send
            if connection.index > I_PDU.SDULength() + 63:
                connection.transmiting = False
                connection.sequence = 0
                connection.index = 0
 
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.stage = Connection_Stage.SENT_CF
 
    # Send FLOW CONTROL
    def transmitFC(self, BS, STmin, FS : FS_t):
        FC_SDU = [((0x03 << 4 )|FS), BS, STmin] + [0] * 5
        FC = I_PDU(0x11, SDU = FC_SDU, is_FD = False)
        self.bus.send(FC)
       
 
""" ===========================================================================================
Module              : TP_Receive
Brief               : Class derived by can.Listener
Note                : - Construction with transmit interface, BS, STmin
=========================================================================================== """
class TP_Receive(can.Listener):
    ''' Constructor '''
    def __init__(self, connections_R : List[Can_TP_Connection]) -> None:
        self.received_data = []                             # Array for storing massage
        self.connections_R = connections_R
 
    # Override on_message_received
    def on_message_received(self, msg: can.Message) -> None:
        # Check whether the connection already existed or not
        connection = next((conn for conn in self.connections_R if msg.arbitration_id == conn.connectionID), None)
 
        # Create new connection if it doesn't exist
        if connection is None:
            connection = Can_TP_Connection(connectionID = msg.arbitration_id)
            self.connections_R.append( connection )
 
        if msg.is_fd == True:
            self.process_CanFD(msg, connection)
        else:
            self.process_ClassicCan(msg, connection)
 
        # Completed message
        # if self.receiving == False:
        #     print(self.received_data.decode('utf-8'))
   
    def detectPDU(self, connection : Can_TP_Connection) -> I_PDU:
        global PDU_App_R
        ReValue = None
        for pdu in PDU_App_R:
            if connection.connectionID == pdu.ID:
                ReValue = pdu
                break
        return ReValue
    def process_CanFD(self, N_PDU : can.Message, connection : Can_TP_Connection):
        PCI = N_PDU.data[:2]
        PDU_working = self.detectPDU(connection)
       
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if PCI[0] == 0x00:
                SDU = N_PDU.data[2:]
                data_length = PCI[1]
                PDU_working.SDU = SDU[:data_length]
                connection.receiving = False
 
            # First Frame
            elif 0x10 <= PCI[0] < 0x20:
                connection.expected_length = (N_PDU.data[2] << 24)| (N_PDU.data[3] << 16) | (N_PDU.data[4] << 8) | (N_PDU.data[5])
                PDU_working.SDU = N_PDU.data[2:]
                connection.receiving = True
                connection.sequenceIdx = 1
 
            # Consecutive Frame
            elif 0x20 <= PCI[0] < 0x30 and connection.receiving:
                sequence_number = PCI[0] & 0x0F
                SDU = N_PDU.data[1:]
                if connection.sequenceIdx == sequence_number:
                    # Store data
                    PDU_working.SDU += SDU
 
                    connection.sequenceIdx += 1
                    if connection.sequenceIdx >= 16:
                        connection.sequenceIdx = 0
                   
                    if len(PDU_working.SDU) >= connection.expected_length:
                        connection.receiving = False
                        connection.sequenceIdx = 0
 
    def process_ClassicCan(self, N_PDU : can.Message, connection : Can_TP_Connection):
        PCI = N_PDU.data[0]
        SDU = N_PDU.data[1:]
        PDU_working = self.detectPDU(connection)
       
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if PCI <= 0x07:
                data_length = PCI
                PDU_working.SDU = SDU[:data_length]
                connection.receiving = False
               
            # First Frame
            elif 0x10 <= PCI < 0x20:
                connection.expected_length = ((PCI & 0x0F) << 8) | N_PDU.data[1]
                PDU_working.SDU = N_PDU.data[2:]
                connection.receiving = True
                connection.sequenceIdx = 1
 
            # Consecutive Frame
            elif 0x20 <= PCI < 0x30 and self.receiving:
                sequence_number = PCI & 0x0F
 
                if connection.sequenceIdx == sequence_number:
                    # Store data
                    PDU_working.SDU += SDU
 
                    connection.sequenceIdx += 1
                    if connection.sequenceIdx >= 16:
                        connection.sequenceIdx = 0
 
                    # Finish receive a completed message
                    if len(PDU_working.SDU) >= connection.expected_length:
                        connection.receiving = False
                        connection.sequenceIdx = 0
           
            elif 30 <= PCI < 40:
                connection.TP_Config.BS = N_PDU[1]
                connection.TP_Config.STmin = N_PDU[2]
                if (N_PDU[0] & 0x0F) == FS_t.CTS:
                    pass
 