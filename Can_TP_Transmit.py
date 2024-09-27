""" ============================================================================================
Module              : TP_Transmit
Last Modified       : September 27, 2024
Author              : Tran Than
Description         :
    Manages the transmission operations of the CAN Transport Protocol (CAN TP) layer.
    Responsibilities include:
        - Handling transmission requests for CAN TP messages.
        - Managing CAN TP connections for transmitting data.
        - Sending Single Frames, First Frames, Consecutive Frames, and Flow Control messages.
        - Periodically processing and transmitting CAN TP messages based on connection states.
Notes               :
    - Utilizes the `Bus` class from the `Can_LL` module for low-level CAN bus operations.
    - Interacts with `Can_TP_Connection` objects to manage multiple CAN TP connections.
    - Works with PDUs defined in `PDU_App_T` for transmission.
============================================================================================ """
import copy
import time
from typing import List
from PDUs import PDU_App_T
from Common import I_PDU, Connection_Stage, Connection_Type, TimeoutType, MessageFrame_Type
from Can_LL import Bus
from Can_TP_Connection import Can_TP_Connection
 
class Can_TP_Transmit:
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
        N_PDU = copy.deepcopy(I_PDU)
 
        # Message Frame: Type 2
        if connection.messageFrame == MessageFrame_Type.TYPE_2:
            N_PCI = [(0x01 << 4 | (SDULength >> 8)), (SDULength & 0xFF)]
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