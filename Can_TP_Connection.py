""" ================================================================================================
Module              : TP_Receive
Last Modified       : September 27, 2024
Author              : Tran Than
Description         :
    Defines configuration and connection management classes for the CAN Transport Protocol (CAN TP)
    reception operations. These classes handle the setup and state management required for
    receiving CAN TP messages, including timeout configurations and connection classifications.
Notes:
================================================================================================ """
import time
from PDUs import PDU_App_T
from Common import Connection_Stage, Connection_Type, TimeoutType, MessageFrame_Type, FS_t
 
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
        self.done = True
           
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
 