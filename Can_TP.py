import can
import copy
import time
from Common import I_PDU, N_PDU
from Can_LL import Bus
 
""" ===========================================================================================
Module              : Can_TP
Brief               : Main module for Can-TP
=========================================================================================== """
class Can_TP:
    ''' Constructor '''
    def __init__(self):
        self.BS = 5
        self.STmin = 1
 
        self.LL_bus = Bus()
        self.transmitState = Can_TP_Transmit_State()
        self.receiveState = Can_TP_Receive_State()
        self.TP_transmit = TP_Transmit(self.LL_bus)
        self.TP_receive = TP_Receive(self.TP_transmit, self.BS, self.STmin)
 
    ''' Destructor '''
    def __del__(self):
        print("Destructor: CanTP")
        # pass
 
    def init(self):
        # Init Can LL
        self.LL_bus.init()
 
    def startListen(self):
        self.LL_bus.startListen(self.TP_receive)
        self.receiveState.receiving = True
   
    def transmitMessage(self, I_PDU : I_PDU):
        self.LL_bus.stopListen()
 
        # Send SF
        if I_PDU.SDULength() <= 7 or (I_PDU.SDULength() <= 62 and I_PDU.is_FD == True):
            self.TP_transmit.transmitSF(I_PDU)
       
        # Send Segmentation
        else:
            self.TP_transmit.transmitFF(I_PDU, self.transmitState)
 
            while self.transmitState.transmiting is True:
                self.TP_transmit.transmitCF(I_PDU, self.transmitState)
                time.sleep(0.01)
 
        if self.receiveState.receiving is True:
            self.LL_bus.startListen(self.TP_receive)
 
""" ===========================================================================================
Module              : TP_Transmit
Brief               : Module provides method for handling transmiting operation
                    of Can-TP layer
============================================================================================"""
class Can_TP_Transmit_State:
        def __init__(self):
            self.transmiting = False
            self.sequence = 0
            self.index = 0
 
class TP_Transmit:
    ''' Constructor '''
    def __init__(self, bus : Bus):
        # print("Constructor: CanTP Transmit")
        self.bus = bus
 
    ''' Destructor '''
    def __del__(self):
        # print("Destructor: CanTP Transmit")
        pass
 
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
    def transmitFF(self, I_PDU : I_PDU, state : Can_TP_Transmit_State):
        SDULength = I_PDU.SDULength()
        N_PDU = copy.deepcopy(I_PDU)
        state.transmiting = True
 
        if(I_PDU.is_FD is not True):
            # Classical Can
            N_PCI = [(0x01 << 4 | (SDULength >> 8)), (SDULength & 0xFF)]
            N_SDU = I_PDU.SDU[:6]
            state.index = 13
        else:
            # Can FD
            N_PCI = [(0x01 << 4), 0x00, (SDULength >> 24 & 0xFF),(SDULength >> 16 & 0xFF), (SDULength >> 8 & 0xFF), (SDULength & 0xFF)]
            N_SDU = I_PDU.SDU[:58]              # 64 - 6 PCI bytes
            state.index = 121
       
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
       
    # Send CONSECUTIVE FRAME
    def transmitCF(self, I_PDU : I_PDU, state : Can_TP_Transmit_State):
        N_PDU = copy.deepcopy(I_PDU)
 
        state.sequence += 1
        if state.sequence >= 16:
            state.sequence = 0
 
        N_PCI = [0x02 << 4 | (state.sequence & 0x0F)]
 
        if(I_PDU.is_FD is not True):
            # Classical Can
            N_SDU = I_PDU.SDU[state.index - 7 : state.index]
            state.index += 7
            # Completely send
            if state.index > I_PDU.SDULength() + 7:
                state.transmiting = False
                state.sequence = 0
                state.index = 0
        else:
            # Can FD
            N_SDU = I_PDU.SDU[state.index - 63 : state.index]
            state.index += 63
            # Completely send
            if state.index > I_PDU.SDULength() + 63:
                state.transmiting = False
                state.sequence = 0
                state.index = 0
 
        N_PDU.SDU = list(N_PCI) + list(N_SDU)
        self.bus.send(N_PDU)
 
    # Send FLOW CONTROL
    def transmitFC(self, BS, STmin, FS):
        FC_SDU = [((0x03 << 4 )|FS), BS, STmin] + [0] * 5
        FC = I_PDU(0x11, SDU = FC_SDU, is_FD = False)
        self.trans.transmitMessage(FC)
       
       
""" ===========================================================================================
Module              : TP_Receive
Brief               : Class derived by can.Listener
Note                : - Construction with transmit interface, BS, STmin
=========================================================================================== """
class Can_TP_Receive_State:
        def __init__(self):
            self.receiving = False
 
class TP_Receive(can.Listener):
    def __init__(self, trans : TP_Transmit, BS, STmin) -> None:
        self.received_data = []                             # Array for storing massage
        self.expected_length = 0                            # Length of message (include data in  FF and CF)
        self.receiving = False
       
        self.trans = trans
        self.BS = BS
        self.STmin = STmin
        self.sequenceIdx = 0
 
    # Override on_message_received
    def on_message_received(self, msg: can.Message) -> None:
        if msg.is_fd == True:
            self.process_CanFD(msg)
        else:
            self.process_ClassicCan(msg)
 
        if self.receiving == False:
            print(self.received_data.decode('utf-8'))
           
    def process_CanFD(self, N_PDU : can.Message):
        PCI = N_PDU.data[:2]
 
        # Single Frame
        if PCI[0] == 0x00:
            SDU = N_PDU.data[2:]
            data_length = PCI[1]
            self.received_data = SDU[:data_length]
            self.receiving = False
 
        # First Frame
        elif 0x10 <= PCI[0] < 0x20:
            self.expected_length = (N_PDU.data[2] << 24)| (N_PDU.data[3] << 16) | (N_PDU.data[4] << 8) | (N_PDU.data[5])
            self.received_data = N_PDU.data[2:]
            self.receiving = True
            self.sequenceIdx = 1
 
        # Consecutive Frame
        elif 0x20 <= PCI[0] < 0x30 and self.receiving:
            sequence_number = PCI[0] & 0x0F
            SDU = N_PDU.data[1:]
            if self.sequenceIdx == sequence_number:
                # Store data
                self.received_data += SDU
 
                self.sequenceIdx += 1
                if self.sequenceIdx >= 16:
                    self.sequenceIdx = 0
               
                if len(self.received_data) >= self.expected_length:
                    self.receiving = False
                    self.sequenceIdx = 0
 
    def process_ClassicCan(self, N_PDU : can.Message):
        PCI = N_PDU.data[0]
        SDU = N_PDU.data[1:]
        # Single Frame
        if PCI <= 0x07:
            data_length = PCI
            self.received_data = SDU[:data_length]
            self.receiving = False
           
        # First Frame
        elif 0x10 <= PCI < 0x20:
            self.expected_length = ((PCI & 0x0F) << 8) | N_PDU.data[1]
            self.received_data = N_PDU.data[2:]
            self.receiving = True
            self.sequenceIdx = 1
       
        # Consecutive Frame
        elif 0x20 <= PCI < 0x30 and self.receiving:
            sequence_number = PCI & 0x0F
 
            if self.sequenceIdx == sequence_number:
                # Store data
                self.received_data += SDU
 
                self.sequenceIdx += 1
                if self.sequenceIdx >= 16:
                    self.sequenceIdx = 0
 
                # Finish receive a completed message
                if len(self.received_data) >= self.expected_length:
                    self.receiving = False
                    self.sequenceIdx = 0
 
 