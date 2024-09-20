import time
from PDUs import PDU_App_T, PDU_App_R
from typing import List
from Can_TP import Can_TP , Can_TP_Connection
 
 
if __name__ == "__main__":
    myMachine = Can_TP()
    myMachine.init()
 
    # myMachine.startListen()
    # myMachine.transmitMessage(PDU_App_T[0])
    # myMachine.transmitMessage(PDU_App_T[0])
    # for x in range(1, 6):
    while 1:
    #     time.sleep(8)
        # print(PDU_App_T[1].SDU)
        # myMachine.transmitMessage(PDU_App_T[0])
        # print("mess 1")
        # time.sleep(5)
        # myMachine.transmitMessage(PDU_App_T[1])
        # print("mess 2")
        # time.sleep(5)
        # myMachine.transmitMessage(PDU_App_T[2])
        # print("mess 3")
        # time.sleep(5)
        # myMachine.transmitMessage(PDU_App_T[3])
        # print("mess 4")
        # time.sleep(5)
        # myMachine.transmitMessage(PDU_App_T[4])
        # print("mess 5")
        # time.sleep(5)
        myMachine.transmitMessage(PDU_App_T[4])
        time.sleep(5)