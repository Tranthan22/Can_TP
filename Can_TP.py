""" ================================================================================================
Module              : Can_TP
Last Modified       : September 27, 2024
Author              : Tran Than
Description         : Main module for CAN Transport Protocol (CAN TP) handling.
Notes               :
================================================================================================ """
import threading
from typing import List
from Common import I_PDU
from Can_LL import Bus
from Can_TP_Transmit import Can_TP_Transmit
from Can_TP_Receive import  Can_TP_Receive
from Can_TP_Connection import Can_TP_Connection
 
class Can_TP:
    # Constructor
    def __init__(self):
        self.LL_bus = Bus()
        self.connections : List[Can_TP_Connection] = []
        self.TP_transmit = Can_TP_Transmit(self.LL_bus, self.connections)
        self.TP_receive = Can_TP_Receive(self.connections)
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
 