""" ============================================================================================
Module              : TP_Receive
Last Modified       : September 27, 2024
Author              : Tran Than
Description         :
    Handles the reception and processing of CAN Transport Protocol (CAN TP) messages.
    Responsibilities include:
        - Listening for incoming CAN messages.
        - Managing CAN TP connections.
        - Processing Single Frames, First Frames, Consecutive Frames, and Flow Control messages.    
Notes               :
    - Inherits from `can.Listener` provided by the `python-can` library.
    - Overrides the `on_message_received` method to implement custom message handling.
============================================================================================ """
import can
import time
from typing import List
from PDUs import PDU_App_R
from Common import I_PDU, Connection_Stage, Connection_Type, TimeoutType, FS_t
from Can_TP_Connection import Can_TP_Connection
 
class Can_TP_Receive(can.Listener):
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
                self.connections.append( connection )
                print("Create a connection for receiving")
 
            if connection.connectionType == Connection_Type.RECEIVER:
                if self.detectPDU(connection) is not None:
                    if msg.is_fd == True:
                        self.processCanFD(msg, connection)
                    else:
                        self.processClassicCan(msg, connection)
                else:
                    connection.done = True # Abort connection caused by PDU existence
            elif connection.connectionType == Connection_Type.TRANSMITER:
                self.processFC(msg, connection)
            else:
                pass
   
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