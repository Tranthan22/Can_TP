from enum import Enum
 
class I_PDU:
    def __init__(self, ID = 0, SDU = None, is_ExtendedID = False, is_FD = False, bitrate_sw = False):
        self.ID = ID
        self.SDU =  SDU
        self.is_ExtendedID = is_ExtendedID
        self.is_FD = is_FD
        self.bitrate_sw = bitrate_sw
 
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
 
class TimeoutType(Enum):
    N_As            = 0
    N_Bs            = 1
    N_Cs            = 2
    N_Ar            = 3
    N_Br            = 4
    N_Cr            = 5