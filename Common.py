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
 
class Connection_State(Enum):
    TRANSMIT_STATE      = 0
    RECEIVING_STATE     = 1
    IDLE_STATE          = 2
 
class Connection_Stage(Enum):
    UNKNOW_STATE            = -1
    SENT_FF                 = 0
    SENDING_CF_CONTINOUS    = 1
    SENDING_CF_WAIT         = 2
    SENT_CF                 = 3
    SENT_FC                 = 4
 
    RECEIVED_FF             = 5
    RECEIVING_CF            = 6