# CanTP layer implemented by python based on Autosar & ISO 15765-2

## Purpose
This project is designed just only in experiment, mainly for testing

## Main feature
- **Classification:** Works well with both Classical CAN and CAN FD
- **Segmentation, Reassembly:** Fully meet requirements of transportation layer
- **Session:** Handles session for connection
- **Multi connection:** Deals with multiple connections simultaneously (multiple segmentation sessions in parallel)
- **Configuable:** Parameter could be configuable, providing ability to simulate cases
- **Lock Upper layer's buffer:** Provide API to lock buffer of upper layer (not done)

## Equipments
- Experiment with ValueCAN 4

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

## Hardware setup
<div align="center">
  <img src="https://github.com/user-attachments/assets/a2bc839d-06ba-4c76-993b-847e257f563c" alt="abc" style="transform: rotate(90deg);" width = "400"/>
</div>

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
