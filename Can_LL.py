""" ============================================================================================
Module              : Bus
Last Modified       : September 27, 2024
Author              : Tran Than
Description         :
    Manages CAN bus communication using the Python-CAN library.
    Responsibilities include:
        - Initializing and shutting down the CAN bus.
        - Transmitting CAN frames.
        - Listening for incoming CAN frames and handling callbacks.
        - Managing the CAN notifier for asynchronous message reception.
Notes               :
============================================================================================ """
import can
from Common import N_PDU
class Bus:
    """ Constructor """
    def __init__(self):
        self.bus = None
        self.notifier = None
        self.RxHandle = None
 
    """ Destructor """
    def __del__(self):
        print("Destructor: CanLL")
 
    """ Initialize bus """
    def init(self, interface = 'neovi', channel = 1, bitrate = 500000, receive_own_messages = False):
        # Stop bus
        if self.bus is not None:
            self.stopBus()
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
 
        try:
            msg = can.Message(
                arbitration_id = N_PDU.ID,
                data = N_PDU.SDU,
                is_extended_id = N_PDU.isExtendedID,
                is_fd = N_PDU.isFD
            )
            self.bus.send(msg)
            print(f"Transmit {msg}")
 
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
            print("Stop listen")