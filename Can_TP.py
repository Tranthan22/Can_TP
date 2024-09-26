import can
import copy
import time
import threading
from typing import List
from PDUs import PDU_App_T, PDU_App_R
from Common import I_PDU, N_PDU, FS_t, Connection_Stage, Connection_Type, TimeoutType, MessageFrame_Type
from Can_LL import Bus
 
 
""" ===========================================================================================
Module              : Can_TP
Brief               : Main module for Can-TP
=========================================================================================== """
class Can_TP_Config:
    def __init__(self, BS, STmin, N_A, N_B, N_C):
        self.FS = FS_t.CTS
        self.BS = BS
        self.STmin = STmin
 
        """
        N_As: Time for transmission of the CAN frame(any N_PDU) on the sender side
        N_Ar: Time for transmission of the CAN frame (any N_PDU) on the receiver side"""
        self.N_A = N_A
       
        """
        N_Bs: Time until reception of the next FlowControl N_PDU
        N_Br: Time until transmission of the next FlowControl N_PDU"""
        self.N_B = N_B
       
        """
        N_Cs Time until transmission of the next ConsecutiveFrame N_PDU
        N_Cr Time until reception of the next Consecutive Frame N_PDU"""
        self.N_C = N_C
 
class Can_TP_Connection:
    def __init__(self, connectionID, connectionType : Connection_Type, BS = 5, STmin = 10, N_A = 2, N_B = 2, N_C = 2):
        self.TP_Config = Can_TP_Config(BS, STmin, N_A, N_B, N_C)
        self.connectionID = connectionID               # connectionID is mapping to PDU ID
        # self.I_PDU = I_PDU                          # Reference of I_PDU
        self.connectionType = connectionType        # Type: transmiter/receiver
        self.messageFrame = self.classifyMessFrame()
        self.done = False                           # Mark connection status (Done / not Done)
        self.sequence = 0
        self.index = 0
        self.timingMark = 0                         # Timing mark for STmin
        self.timingoutMark = 0                      # Timing mark for checking timeout
        self.continuousCF = 0                       # Number of receiving/transmitting CF at one time BS
        self.expected_length = 0                    # Length of message (include data in  FF and CF)
        self.waitNum = 0                            # Number of time the receiver sends wait FC
        self.WFTmax = 10                            # Maximum of time the receiver sends wait FC
        self.stage : Connection_Stage = Connection_Stage.UNKNOW_STATE
 
    def classifyMessFrame(self) -> MessageFrame_Type:
        global PDU_App_T
        for pdu in PDU_App_T:
            if pdu.ID == self.connectionID:
                SDULength = pdu.SDULength()
                if SDULength < 8:
                    if pdu.isFD is True:
                        print("type 0")
                        return MessageFrame_Type.TYPE_0
                    else:
                        print("type 1")
                        return MessageFrame_Type.TYPE_1
                elif SDULength < 62:
                    if pdu.isFD is True:
                        print("type 1")
                        return MessageFrame_Type.TYPE_1
                    else:
                        print("type 2")
                        return MessageFrame_Type.TYPE_2
                elif SDULength <= 4095:
                    print("type 2")
                    return MessageFrame_Type.TYPE_2
                else:
                    print("type 3")
                    return MessageFrame_Type.TYPE_3
            else:
                pass
           
    # @classmethod
    # Timing process
    def TimeoutChecking(self, checkingType : TimeoutType) -> bool:
        ReValue = True  # True = TIMEOUT_OK
        if checkingType == TimeoutType.N_As:
            if time.time() - self.timingoutMark > self.TP_Config.N_A:
                self.stage = Connection_Stage.TIMEOUT
                self.done = True
                ReValue = False
                print("Timeout As")
        elif checkingType == TimeoutType.N_Bs:
            if time.time() - self.timingoutMark > self.TP_Config.N_B:
                self.stage = Connection_Stage.TIMEOUT
                self.done = True
                ReValue = False
                print("Timeout Bs")
        elif checkingType == TimeoutType.N_Cs:
            if time.time() - self.timingoutMark > self.TP_Config.N_C:
                self.stage = Connection_Stage.TIMEOUT
                self.done = True
                ReValue = False
                print("Timeout Cs")
        elif checkingType == TimeoutType.N_Ar:
            if time.time() - self.timingoutMark > self.TP_Config.N_A:
                self.stage = Connection_Stage.TIMEOUT
                self.done = True
                ReValue = False
                print("Timeout Ar")
        elif checkingType == TimeoutType.N_Br:
            if time.time() - self.timingoutMark > self.TP_Config.N_B:
                # self.TP_Config.FS = FS_t.WAIT
                self.waitNum += 1
                print("Timeout Br")
                if self.waitNum >= self.WFTmax:
                    self.stage = Connection_Stage.TIMEOUT
                    self.done = True
                    print("Abort session caused timeout Br")
                    return False
            else:
                self.TP_Config.FS = FS_t.CTS
 
        elif checkingType == TimeoutType.N_Cr:
            if time.time() - self.timingoutMark > self.TP_Config.N_C:
                self.stage = Connection_Stage.TIMEOUT
                self.done = True
                ReValue = False
                print("Timeout Cr")
        else:
            pass
 
        # Refresh timing
        self.timingoutMark = time.time()
        return ReValue
 
class Can_TP:
    # Constructor
    def __init__(self):
        self.LL_bus = Bus()
        self.connections : List[Can_TP_Connection] = []
        self.TP_transmit = TP_Transmit(self.LL_bus, self.connections)
        self.TP_receive = TP_Receive(self.connections)
        self.main_thread = None
 
    # Destructor
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
    # Constructor
    def __init__(self, bus : Bus, connections : List[Can_TP_Connection]):
        # print("Constructor: CanTP Transmit")
        self.bus = bus
        self.connections = connections
 
    # Destructor
    def __del__(self):
        # print("Destructor: CanTP Transmit")
        pass
   
    # Create request to send
    def transmit(self, I_PDU : I_PDU):
        connection = Can_TP_Connection(I_PDU.ID, Connection_Type.TRANSMITER)
        self.connections.append( connection )
        connection.timingoutMark = time.time()  # Start N_As
        print("Create a request/connection")
       
    # Transmit mainfunction periodically works
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
                            if (connection.messageFrame == MessageFrame_Type.TYPE_0) or (connection.messageFrame == MessageFrame_Type.TYPE_1):
                                self.transmitSF(pdu, connection)
                            # Send Segmentation
                            else:
                                # Send First frame
                                if connection.stage == Connection_Stage.UNKNOW_STATE:
                                    self.transmitFF(pdu, connection)
                                    connection.TimeoutChecking(TimeoutType.N_As)
 
                                # Send Consecutive frame
                                elif connection.stage == Connection_Stage.SENDING_CF_CONTINOUS:
                                    # Satisfied seperated time
                                    if time.time() - connection.timingMark >= connection.TP_Config.STmin / 1000 :
                                        connection.TimeoutChecking(TimeoutType.N_Cs)
                                        self.transmitCF(pdu, connection)
                                        connection.timingMark = time.time()
                                        connection.TimeoutChecking(TimeoutType.N_As)
 
                                        # Wait after sending BS Consecutive Frame
                                        connection.continuousCF += 1
                                        if connection.continuousCF >= connection.TP_Config.BS:
                                            connection.stage = Connection_Stage.SENDING_CF_WAIT
                                            connection.continuousCF = 0
 
                                # Receiver need more time to get the next segments
                                elif connection.stage == Connection_Stage.SENDING_CF_WAIT:
                                    pass
 
                                else:
                                    pass
                            break
                else:   # Role: Receiver
                    # sending Flow Control message
                    if connection.stage == Connection_Stage.SEND_FC:
                        if connection.TimeoutChecking(TimeoutType.N_Br) is True:
                            self.transmitFC(connection)
                            connection.TimeoutChecking(TimeoutType.N_Ar)
                        else:
                            pass    # Abort session
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
 
        # Message Frame: Type 0
        if connection.messageFrame == MessageFrame_Type.TYPE_0:
            N_PCI = [(0 | SDULength & 0x0F)]
            if I_PDU.isPadding is True:
                N_SDU = list([I_PDU.dummyByte] * (I_PDU.Tx_DL - 1))
                N_SDU[:I_PDU.SDULength()] = list(I_PDU.SDU)
            else:
                N_SDU = list(I_PDU.SDU)
       
        # Message Frame: Type 1
        else:
            N_PCI = [0 , SDULength]            
            N_SDU = list([I_PDU.dummyByte] * (I_PDU.Tx_DL - 2))
            N_SDU[:I_PDU.SDULength] = list(I_PDU.SDU)
 
        N_PDU.SDU = N_PCI + N_SDU
        self.bus.send(N_PDU)
        connection.done = True
 
    # Send FIRST FRAME
    def transmitFF(self, I_PDU : I_PDU, connection : Can_TP_Connection):
        SDULength = I_PDU.SDULength()
        print(SDULength)
        N_PDU = copy.deepcopy(I_PDU)
 
        # Message Frame: Type 2
        if connection.messageFrame == MessageFrame_Type.TYPE_2:
            N_PCI = [(0x01 << 4 | (SDULength >> 8)), (SDULength & 0xFF)]
            print(N_PCI)
            # CAN FD (FF = Tx_DL bytes)
            if I_PDU.isFD is True:
                N_SDU = I_PDU.SDU[:(I_PDU.Tx_DL - 2)]
                connection.index = I_PDU.Tx_DL - 2          # Minus 2 bytes PCI
            # Classical CAN (FF = 8 bytes)
            else:
                N_SDU = I_PDU.SDU[:6]
                connection.index = 6                        # Minus 2 bytes PCI
        # Message Frame: Type 3
        else:
            N_PCI = [(0x01 << 4), 0x00, (SDULength >> 24 & 0xFF),(SDULength >> 16 & 0xFF), (SDULength >> 8 & 0xFF), (SDULength & 0xFF)]
            N_SDU = I_PDU.SDU[:(I_PDU.Tx_DL - 6)]
            connection.index = I_PDU.Tx_DL - 6
       
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.stage = Connection_Stage.SENT_FF
        # print("sent FF")
        connection.done = False
       
    # Send CONSECUTIVE FRAME
    def transmitCF(self, I_PDU : I_PDU, connection : Can_TP_Connection):
        N_PDU = copy.deepcopy(I_PDU)
       
        # N_PCI
        connection.sequence += 1
        if connection.sequence >= 16:
            connection.sequence = 0
        N_PCI = [0x02 << 4 | (connection.sequence & 0x0F)]
 
        # Classical Can
        if(I_PDU.isFD is not True):
            # Last segmentation
            if (connection.index + I_PDU.Tx_DL - 1) > I_PDU.SDULength():
                if I_PDU.isPadding is True:
                    segLength = I_PDU.SDULength() - connection.index
                    N_SDU = list([I_PDU.dummyByte] * (I_PDU.Tx_DL - 1))
                    N_SDU[:segLength] = I_PDU.SDU[connection.index : connection.index + I_PDU.Tx_DL - 1]
                else:
                    N_SDU = I_PDU.SDU[connection.index:]
                # Mark done connection
                connection.done = True
 
            else:
                N_SDU = I_PDU.SDU[connection.index : connection.index + I_PDU.Tx_DL - 1]
                connection.index += (I_PDU.Tx_DL - 1)
        # Can FD
        else:
            # Last segmentation
            if (connection.index + I_PDU.Tx_DL - 1) > I_PDU.SDULength():
                segLength = I_PDU.SDULength() - connection.index
                N_SDU = list([I_PDU.dummyByte] * (I_PDU.Tx_DL - 1))
                N_SDU[:segLength] = I_PDU.SDU[connection.index : connection.index + I_PDU.Tx_DL - 1]
               
                # Mark done connection
                connection.done = True
            else:
                N_SDU = I_PDU.SDU[connection.index : connection.index + I_PDU.Tx_DL - 1]
                connection.index += (I_PDU.Tx_DL - 1)
           
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
        connection.stage = Connection_Stage.SENDING_CF_CONTINOUS
        # print("sent CF")
 
    # Send FLOW CONTROL
    def transmitFC(self, connection : Can_TP_Connection):
        FC_SDU = [((0x03 << 4 )|connection.TP_Config.FS.value), connection.TP_Config.BS, connection.TP_Config.STmin] + [0] * 5
        FC = I_PDU(ID = connection.connectionID, SDU = FC_SDU, isFD = False)
        self.bus.send(FC)
        connection.stage = Connection_Stage.RECEIVING_CF
 
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
        if msg.arbitration_id != 0x00:
            # Check whether the connection already existed or not
            connection = next((conn for conn in self.connections if msg.arbitration_id == conn.connectionID), None)
            print(f"receive {msg}")
 
            # Create new connection if it doesn't exist
            if connection is None:
                connection = Can_TP_Connection(msg.arbitration_id, Connection_Type.RECEIVER)
                connection.stage = Connection_Stage.SEND_FC
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
        FirstByte = N_PDU.data[0]
        SecondByte = N_PDU.data[1]
 
        MsgType = (FirstByte >> 4) & 0x0F
 
        PDU_working = self.detectPDU(connection)
       
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if MsgType == 0x00:
                # Message Frame: Type 0
                if (FirstByte & 0x0F) != 0x00:
                    SDU = N_PDU.data[1:]
                    SF_DL = (FirstByte >> 4) & 0x0F
                    PDU_working.SDU = SDU[:SF_DL]
               
                # Message Frame: Type 1
                else:
                    SDU = N_PDU.data[2:]
                    SF_DL = N_PDU.data[2]
                    PDU_working.SDU = SDU[:SF_DL]
 
                print(connection.stage)
                connection.done = True
 
            # First Frame
            elif MsgType == 0x01:
                connection.stage = Connection_Stage.RECEIVED_FF
                connection.timingoutMark = time.time() # Start N_Br
                FF_DL = ((FirstByte & 0x0F) << 8) | (SecondByte)
                # Message Frame: Type 2
                if FF_DL != 0x00:
                    connection.expected_length = FF_DL
                    PDU_working.SDU = N_PDU.data[2:]
                   
                # Message Frame: Type 3
                else:
                    connection.expected_length = (N_PDU.data[2] << 24)| (N_PDU.data[3] << 16) | (N_PDU.data[4] << 8) | (N_PDU.data[5])
                    PDU_working.SDU = N_PDU.data[6:]
                connection.done = False
                connection.sequence = 1
                connection.stage = Connection_Stage.SEND_FC
 
            # Consecutive Frame
            elif MsgType == 0x02:
                if connection.TimeoutChecking(TimeoutType.N_Cr) is True:
                    sequence_number = FirstByte & 0x0F
                    SDU = N_PDU.data[1:]
                    if connection.sequence == sequence_number:
                        # Store data
                        PDU_working.SDU += SDU
                        connection.stage = Connection_Stage.RECEIVING_CF
                        connection.continuousCF += 1
 
                        # Cycle consequence index
                        connection.sequence += 1
                        if connection.sequence >= 16:
                            connection.sequence = 0
                       
                        # Finish receive a completed message
                        if len(PDU_working.SDU) >= connection.expected_length:
                            PDU_working.SDU = PDU_working.SDU[:connection.expected_length]
                            connection.done = True
                            connection.sequence = 0
                        else:
                            # After BS times receive Consecutive Frame
                            if connection.continuousCF >= connection.TP_Config.BS:
                                connection.stage = Connection_Stage.SEND_FC
                                connection.continuousCF = 0
                else:
                    pass    # Abort session
            else:
                pass
 
    def processClassicCan(self, N_PDU : can.Message, connection : Can_TP_Connection):
        FirstByte = N_PDU.data[0]
        MsgType = (FirstByte >> 4) & 0x0F
 
        PDU_working = self.detectPDU(connection)
 
        if PDU_working is not None:             # Unexpected message
            # Single Frame
            if MsgType == 0x00:
                SF_DL = FirstByte
                PDU_working.SDU = N_PDU.data[1 : SF_DL + 1]
                connection.done = True
               
            # First Frame
            elif MsgType == 0x01:
                SecondByte = N_PDU.data[1]
                FF_DL = ((FirstByte & 0x0F) << 8) | (SecondByte)
                connection.timingoutMark = time.time() # Start N_Br
                connection.expected_length = FF_DL
                PDU_working.SDU = N_PDU.data[2:]
                connection.done = False
                connection.sequence = 1
                connection.stage = Connection_Stage.SEND_FC
 
            # Consecutive Frame
            elif MsgType == 0x02:
                if connection.TimeoutChecking(TimeoutType.N_Cr) is True:
                    sequence_number = FirstByte & 0x0F
 
                    if connection.sequence == sequence_number:
                        # Store data
                        PDU_working.SDU += N_PDU.data[1:]
                        connection.stage = Connection_Stage.RECEIVING_CF
                        connection.continuousCF += 1
 
                        # Cycle consequence index
                        connection.sequence += 1
                        if connection.sequence >= 16:
                            connection.sequence = 0
 
                        # Finish receive a completed message
                        if len(PDU_working.SDU) >= connection.expected_length:
                            PDU_working.SDU = PDU_working.SDU[:connection.expected_length]
                            connection.done = True
                            connection.sequence = 0
                        else:
                            # After BS times receive Consecutive Frame
                            if connection.continuousCF >= connection.TP_Config.BS:
                                connection.stage = Connection_Stage.SEND_FC
                                connection.continuousCF = 0
                else:
                    pass    # Abort session
            else:
                pass
   
    def processFC(self, N_PDU : can.Message, connection : Can_TP_Connection):
        # Checking Bs timeout
        if connection.TimeoutChecking(TimeoutType.N_Bs):
            # Process Flow Control
            connection.TP_Config.BS = N_PDU.data[1]
            connection.TP_Config.STmin = N_PDU.data[2]
            if (N_PDU.data[0] & 0x0F) == FS_t.CTS.value:
                connection.stage = Connection_Stage.SENDING_CF_CONTINOUS
            elif (N_PDU.data[0] & 0x0F) == FS_t.WAIT.value:
                connection.stage = Connection_Stage.SENDING_CF_WAIT
            else:
                pass
        else:
            pass # Abort session