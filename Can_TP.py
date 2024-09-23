import can
import copy
import time
import threading
from typing import List
from PDUs import PDU_App_T, PDU_App_R
from Common import I_PDU, N_PDU, FS_t, Connection_Stage, Connection_Type
from Can_LL import Bus
 
 
""" ===========================================================================================
Module              : Can_TP
Brief               : Main module for Can-TP
=========================================================================================== """
class Can_TP_Config:
    def __init__(self, BS = 5, STmin = 0.01):
        self.FS = FS_t.CTS
        self.BS = BS
        self.STmin = STmin
 
class Can_TP_Connection:
    def __init__(self, connectionID, connectionType : Connection_Type):
        self.TP_Config = Can_TP_Config()
        self.connectionID = connectionID
        self.connectionType = connectionType
        self.done = False               # Mark connection status (Done / not Done)
        self.sequence = 0
        self.index = 0
        self.sequenceIdx = 0
        self.timingMark = 0
        self.expected_length = 0        # Length of message (include data in  FF and CF)
        self.stage : Connection_Stage = Connection_Stage.UNKNOW_STATE
 
class Can_TP:
    ''' Constructor '''
    def __init__(self):
        self.LL_bus = Bus()
        self.connections : List[Can_TP_Connection] = []
        self.TP_transmit = TP_Transmit(self.LL_bus, self.connections)
        self.TP_receive = TP_Receive(self.connections)
        self.main_thread = None
 
    ''' Destructor '''
    def __del__(self):
        self.LL_bus.stopListen()
        self.LL_bus.stopBus()
        self.LL_bus.__del__()
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
    def __init__(self, bus : Bus, connections : List[Can_TP_Connection]):
        # print("Constructor: CanTP Transmit")
        self.bus = bus
        self.connections = connections
 
    ''' Destructor '''
    def __del__(self):
        # print("Destructor: CanTP Transmit")
        pass
   
    """ Create request to send """
    def transmit(self, I_PDU : I_PDU):
        self.connections.append( Can_TP_Connection(I_PDU.ID, Connection_Type.TRANSMITER))
        print("Create a request/connection")
       
    """ Transmit mainfunction periodically works """
    def Main_Fuction(self):
        global PDU_App_T
        while 1:
            connectionsAtTime = self.connections
            connecitonShallRemove = []
 
            # Operate with every connection
            for connection in connectionsAtTime:
                if connection.connectionType == Connection_Type.TRANSMITER: # Role: Transmitter
                    # Finding the PDU which the connection works with
                    for pdu in PDU_App_T:
                        if connection.connectionID == pdu.ID:
                            # Send SF
                            if pdu.SDULength() <= 7 or (pdu.SDULength() <= 62 and pdu.is_FD == True):
                                self.transmitSF(pdu, connection)
 
                            # Send Segmentation
                            else:
                                print(connection.stage)
                                # Send First frame
                                if connection.stage == Connection_Stage.UNKNOW_STATE:
                                    self.transmitFF(pdu, connection)
                                   
                                # Send Consecutive frame
                                elif (connection.stage == Connection_Stage.SENDING_CF_CONTINOUS) or (connection.stage == Connection_Stage.SENT_FF):
                                    # Satisfied seperated time
                                    if time.time() - connection.timingMark > connection.TP_Config.STmin:
                                        self.transmitCF(pdu, connection)
                                        connection.timingMark = time.time()
 
                                # Receiver need more time to get the next components
                                elif connection.stage == Connection_Stage.SENDING_CF_WAIT:
                                    pass
 
                                else:
                                    pass
                            break
                else:   # Role: Receiver
                    # Receiver sends Flow Control message
                    if connection.stage == Connection_Stage.SEND_FC:
                        self.transmitFC(pdu, connection)
                    else:
                        pass
 
                # Connection works done
                if connection.done is True:
                    connecitonShallRemove.append(connection)
 
            # Remove connection from list of requests
            for connection in connecitonShallRemove:
                if connection in self.connections:
                    self.connections.remove(connection)
                    print("A connection have been deleted")
           
            # Time cycle
            time.sleep(0.001)
           
    # Send SINGLE FRAME
    def transmitSF(self, I_PDU : I_PDU, connection : Can_TP_Connection):
        SDULength = I_PDU.SDULength()
        N_PDU = copy.deepcopy(I_PDU)
        N_SDU = I_PDU.SDU
 
        if(I_PDU.is_FD is not True):
            N_PCI = [(0 | SDULength & 0x0F)]       # Classic CAN
        else:
            N_PCI = [0 , SDULength]         # Can FD
 
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.done = True
        print("sent SF")
 
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
        print("sent FF")
        connection.done = False
       
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
                connection.done = True
                connection.sequence = 0
                connection.index = 0
        else:
            # Can FD
            N_SDU = I_PDU.SDU[connection.index - 63 : connection.index]
            connection.index += 63
            # Completely send
            if connection.index > I_PDU.SDULength() + 63:
                connection.done = True
                connection.sequence = 0
                connection.index = 0
 
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.stage = Connection_Stage.SENDING_CF_CONTINOUS
        print("sent CF")
 
    # Send FLOW CONTROL
    def transmitFC(self, connection : Can_TP_Connection):
        FC_SDU = [((0x03 << 4 )|connection.TP_Config.FS), connection.TP_Config.BS, connection.TP_Config.STmin] + [0] * 5
        FC = I_PDU(0x11, SDU = FC_SDU, is_FD = False)
        self.bus.send(FC)
       
 
""" ===========================================================================================
Module              : TP_Receive
Brief               : Class derived by can.Listener
Note                : - Construction with transmit interface, BS, STmin
=========================================================================================== """
class TP_Receive(can.Listener):
    ''' Constructor '''
    def __init__(self, connections : List[Can_TP_Connection]) -> None:
        self.received_data = []                             # Array for storing massage
        self.connections = connections
 
    # Override on_message_received
    def on_message_received(self, msg: can.Message) -> None:
        # Check whether the connection already existed or not
        connection = next((conn for conn in self.connections if msg.arbitration_id == conn.connectionID), None)
 
        # Create new connection if it doesn't exist
        if connection is None:
            connection = Can_TP_Connection(msg.arbitration_id, Connection_Type.RECEIVER)
            # connection.stage =
            self.connections.append( connection )
            print("Create a connection for receiving")
 
        if connection.connectionType == Connection_Type.RECEIVER:
            if msg.is_fd == True:
                self.processCanFD(msg, connection)
            else:
                self.processClassicCan(msg, connection)
        elif connection.connectionType == Connection_Type.TRANSMITER:
            self.processFC(msg, connection)
        else:
            pass
           
 
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
        return ReValue  # Return reference of IPDU which connection works with
   
    def processCanFD(self, N_PDU : can.Message, connection : Can_TP_Connection):
        PCI = N_PDU.data[:2]
        PDU_working = self.detectPDU(connection)
       
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if PCI[0] == 0x00:
                SDU = N_PDU.data[2:]
                data_length = PCI[1]
                PDU_working.SDU = SDU[:data_length]
                connection.done = True
 
            # First Frame
            elif 0x10 <= PCI[0] < 0x20:
                connection.expected_length = (N_PDU.data[2] << 24)| (N_PDU.data[3] << 16) | (N_PDU.data[4] << 8) | (N_PDU.data[5])
                PDU_working.SDU = N_PDU.data[2:]
                connection.done = False
                connection.sequenceIdx = 1
                connection.stage = Connection_Stage.RECEIVED_FF
 
            # Consecutive Frame
            elif 0x20 <= PCI[0] < 0x30:
                sequence_number = PCI[0] & 0x0F
                SDU = N_PDU.data[1:]
                if connection.sequenceIdx == sequence_number:
                    # Store data
                    PDU_working.SDU += SDU
                    connection.stage = Connection_Stage.RECEIVING_CF
                    connection.sequenceIdx += 1
                    if connection.sequenceIdx >= 16:
                        connection.sequenceIdx = 0
                   
                    if len(PDU_working.SDU) >= connection.expected_length:
                        connection.done = True
                        connection.sequenceIdx = 0
            else:
                pass
 
    def processClassicCan(self, N_PDU : can.Message, connection : Can_TP_Connection):
        PCI = N_PDU.data[0]
        SDU = N_PDU.data[1:]
        PDU_working = self.detectPDU(connection)
 
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if PCI <= 0x07:
                data_length = PCI
                PDU_working.SDU = SDU[:data_length]
                connection.done = True
               
            # First Frame
            elif 0x10 <= PCI < 0x20:
                connection.expected_length = ((PCI & 0x0F) << 8) | N_PDU.data[1]
                PDU_working.SDU = N_PDU.data[2:]
                connection.done = False
                connection.sequenceIdx = 1
                connection.stage = Connection_Stage.RECEIVED_FF
 
            # Consecutive Frame
            elif 0x20 <= PCI < 0x30:
                sequence_number = PCI & 0x0F
 
                if connection.sequenceIdx == sequence_number:
                    # Store data
                    PDU_working.SDU += SDU
                    connection.stage = Connection_Stage.RECEIVING_CF
                    connection.sequenceIdx += 1
                    if connection.sequenceIdx >= 16:
                        connection.sequenceIdx = 0
 
                    # Finish receive a completed message
                    if len(PDU_working.SDU) >= connection.expected_length:
                        connection.done = True
                        connection.sequenceIdx = 0
            else:
                pass
   
    def processFC(self, N_PDU : can.Message, connection : Can_TP_Connection):
        connection.TP_Config.BS = N_PDU[1]
        connection.TP_Config.STmin = N_PDU[2]
        if (N_PDU[0] & 0x0F) == FS_t.CTS:
            connection.stage = Connection_Stage.SENDING_CF_CONTINOUS
        elif (N_PDU[0] & 0x0F) == FS_t.WAIT:
            connection.stage = Connection_Stage.SENDING_CF_WAIT
        else:
            pass