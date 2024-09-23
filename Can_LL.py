import can
import time
from Common import N_PDU
 
""" ===========================================================================================
Module              : Bus
Brief               : This module works on bus using PYTHON-CAN api to implement
=========================================================================================== """
class Bus:
    """ Constructor """
    def __init__(self):
        self.bus = None
        self.notifier = None
        self.RxHandle = None
 
    """ Destructor """
    def __del__(self):
        self.stopListen()
        self.stopBus()
        # print("Destructor: CanLL")
 
    """ Initialize bus """
    def init(self, interface = 'neovi', channel = 1, bitrate = 1000000, receive_own_messages = False):
        # Stop bus
        if self.bus is not None:
            self.stop()
        try:
            self.bus = can.Bus(interface=interface, channel=channel, bitrate=bitrate, receive_own_messages = receive_own_messages)
 
        except can.CanError as e:
            print(f'Error bus: {e}')
            self.bus = None
 
    """ Stop bus """
    def stopBus(self):
        if self.bus is not None:
            self.bus.shutdown()
            self.bus = None
            print("Stop bus")
 
    """ Transmit a CAN frame """
    def send(self, N_PDU : N_PDU):
        if self.bus is None:
            print("Bus has not been initialized")
        # print(N_PDU.ID)
        try:
            msg = can.Message(
                arbitration_id = N_PDU.ID,
                data = N_PDU.SDU,
                is_extended_id = N_PDU.is_ExtendedID,
                is_fd = N_PDU.is_FD
            )
            print(f"transmit: {msg}")
            self.bus.send(msg)

        except Exception as e:
            print(f"Error send: {e}")
 
    """ Listen CAN frame """
    def startListen(self, callback = None):
        self.RxHandle = callback
        if self.RxHandle is not None:
            self.notifier = can.Notifier(self.bus, [self.RxHandle])
    
    """ Stop Listening """
    def stopListen(self):
        if self.notifier is not None:
            self.notifier.stop()
            # print("Stop listen")