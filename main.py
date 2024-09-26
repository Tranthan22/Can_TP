import time
from PDUs import PDU_App_T, PDU_App_R
from typing import List
from Can_TP import Can_TP , Can_TP_Connection
 
 
if __name__ == "__main__":
    myMachine = Can_TP()
    myMachine.init()
 
    myMachine.startListen()
   
 
    while 1:
        choice = input()
        if choice == "show":
            if (PDU_App_R[0].SDU) is not None:
                print("I-PDU with ID = 444:")
                print((PDU_App_R[0].SDU).decode('utf-8'))
            if (PDU_App_R[1].SDU) is not None:
                print("I-PDU with ID = 555:")
                print((PDU_App_R[1].SDU).decode('utf-8'))
            if (PDU_App_R[2].SDU) is not None:
                print("I-PDU with ID = 666:")
                print((PDU_App_R[2].SDU).decode('utf-8'))
            if (PDU_App_R[3].SDU) is not None:
                print("I-PDU with ID = 777:")
                print((PDU_App_R[3].SDU).decode('utf-8'))
            if (PDU_App_R[4].SDU) is not None:
                print("I-PDU with ID = 888:")
                print((PDU_App_R[4].SDU).decode('utf-8'))
            if (PDU_App_R[5].SDU) is not None:
                print("I-PDU with ID = 999:")
                print((PDU_App_R[5].SDU).decode('utf-8'))
        elif choice == "mode1":
            myMachine.transmitMessage(PDU_App_T[0])
 
        elif choice == "mode2":
            myMachine.transmitMessage(PDU_App_T[0])
            myMachine.transmitMessage(PDU_App_T[2])
 