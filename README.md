# CanTP layer implemented by python based on Autosar & ISO 15765-2

## Purpose
This project is designed just only in experiment, mainly for testing

## Main feature
- **Classification:** Works well with both Classical CAN and CAN FD
- **Segmentation, Reassembly:** Fully meet requirements of transportation layer
- **Frame support:** Includes SF(single frame), FF(First Frame), CF(Consecutive Frame), FC(Flow Control) following ISO 15765-2
- **Session:** Handles session for connection
- **Multi connection:** Deals with multiple connections simultaneously (multiple segmentation sessions in parallel)
- **Configuable:** Parameter could be configuable, providing ability to simulate cases
- **Lock Upper layer's buffer:** Provide API to lock buffer of upper layer (not done)

## Equipments
- Experiment with ValueCAN 4

![image](https://github.com/user-attachments/assets/0f685789-c97c-49ce-b58f-2014c1b30af8)

## Software
- `Python 3.9`
- `Python-Can` 
- `Python_ics`
- `Filelock`


## Requirements
- pip install python-can
- pip install ics
- pip install filelock
- Driver `icsneo40.dll` (source: https://intrepidcs.com/products/software/vehicle-spy/vehicle-spy-evaluation/)

## Class diagram

![image](https://github.com/user-attachments/assets/30ae3e47-21f2-4c97-a529-2f436b92a03a)


- **Can_TP:** Main module for CAN Transport Protocol (CAN TP) handling.
- **Can_TP_Transmit:** Manages the transmission operations of the CAN Transport Protocol (CAN TP) layer.
- **Can_TP_Receive:** Handles the reception and processing of CAN Transport Protocol (CAN TP) messages.
- **Can_TP_Connection:** Defines configuration and connection management classes for CAN TP reception operations. These classes handle the setup and state management required for receiving CAN TP messages, including timeout configurations and connection classifications.
- **LL_Bus** Manages CAN bus communication using the Python-CAN library.
- **I_PDU** Presents I_PDU

## User guide
1. I-PDU Declaration

`transmitting I-PDU` is declared within list in PDU.py file
```python
PDU_App_T = [
    I_PDU(ID = 0x88, SDU = data.encode('utf-8'), is_FD = True),
    I_PDU(ID = 0x89, SDU = "Hello".encode('utf-8'), is_FD = True),
    I_PDU(ID = 0x90, SDU = data.encode('utf-8'), is_FD = True),
]
```

`receiving I-PDU` is declared within list in PDU.py file
```python
PDU_App_R = [
    I_PDU(ID = 0x88),
    I_PDU(ID = 0x89),
    I_PDU(ID = 0x90),
    I_PDU(ID = 0x91),
]
```
2. Initialization
```python
myMachine = Can_TP()
myMachine.init()
```
3. Create transmitting requests
```python
myMachine.transmitMessage(PDU_App_T[0])
```
