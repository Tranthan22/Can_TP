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