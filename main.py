import time
from PDUs import PDU_App_T, PDU_App_R
from typing import List
from Can_TP import Can_TP , Can_TP_Connection
 
 
if __name__ == "__main__":
    myMachine = Can_TP()
    myMachine.init()
 
    myMachine.startListen()
    # myMachine.transmitMessage(PDU_App_T[0])
    # myMachine.transmitMessage(PDU_App_T[0])
    # for x in range(1, 6):
    while 1:
        # time.sleep(8)
        
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
        # myMachine.transmitMessage(PDU_App_T[4])
        # time.sleep(5)

        if (PDU_App_R[0].SDU) is not None:
            print("111111111111111111111111111111111")
            print((PDU_App_R[0].SDU).decode('utf-8'))
        if (PDU_App_R[1].SDU) is not None:
            print("22222222222222222222222222222222")
            print((PDU_App_R[1].SDU).decode('utf-8'))
        if (PDU_App_R[2].SDU) is not None:
            print("3333333333333333333333333333333333")
            print((PDU_App_R[2].SDU).decode('utf-8'))
        if (PDU_App_R[3].SDU) is not None:
            print("44444444444444444444444444444444444")
            print((PDU_App_R[3].SDU).decode('utf-8'))
        if (PDU_App_R[4].SDU) is not None:
            print("55555555555555555555555555555555555")
            print((PDU_App_R[4].SDU).decode('utf-8'))
        if (PDU_App_R[5].SDU) is not None:
            print("6666666666666666666666666666666666")
            print((PDU_App_R[5].SDU).decode('utf-8'))
        if (PDU_App_R[6].SDU) is not None:
            print("7")
            print((PDU_App_R[6].SDU).decode('utf-8'))
        if (PDU_App_R[7].SDU) is not None:
            print("8")
            print((PDU_App_R[7].SDU).decode('utf-8'))
        time.sleep(3)