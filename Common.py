from enum import Enum
 
class I_PDU:
    def __init__(self, ID = 0, SDU = None, isExtendedID = False, isFD = False, bitrateSW = False, Tx_DL = 8, isPadding = True, BS = 5, STmin = 10, N_A = 2, N_B = 2, N_C = 2):
        self.ID = ID
        self.SDU =  SDU
        self.isExtendedID = isExtendedID
        self.isFD = isFD
        self.bitrateSW = bitrateSW
        self.Tx_DL = Tx_DL
        self.isPadding = isPadding
        self.dummyByte = 0x00
 
        self.BS = BS
        self.STmin = STmin
        self.N_A = N_A
        self.N_B = N_B
        self.N_C = N_C
 
    def SDULength(self) -> int:
        return len(self.SDU)
 
class N_PDU(I_PDU):
    def __init__():
        pass
 
    def SDULength(self) -> int:
        return len(self.SDU)
 
class FS_t(Enum):
    CTS                 = 0
    WAIT                = 1
    OVFLW               = 2
 
class Connection_Type(Enum):
    TRANSMITER          = 0
    RECEIVER            = 1
 
 
class Connection_Stage(Enum):
    TIMEOUT                 = -2
    UNKNOW_STATE            = -1
 
    # Transmitter uses
    SENT_FF                 = 0
    SENDING_CF_CONTINOUS    = 1
    SENDING_CF_WAIT         = 2
   
    # Receiver uses
    RECEIVED_FF             = 6
    RECEIVING_CF            = 7
    SEND_FC                 = 8
 
class MessageFrame_Type(Enum):
    UNKNOWN_TYPE            = -1
    TYPE_0                  = 0         # Single Frame (CAN_DL <= 8)
    TYPE_1                  = 1         # Single Frame (CAN_DL > 8)
    TYPE_2                  = 2         # First Frame (FF_DL <= 4095)
    TYPE_3                  = 3         # First Frame (FF_DL > 4095)
 
class TimeoutType(Enum):
    N_As            = 0
    N_Bs            = 1
    N_Cs            = 2
    N_Ar            = 3
    N_Br            = 4
    N_Cr            = 5