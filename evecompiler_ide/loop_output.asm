; ===== Generated Pseudo-Assembly =====

.data
    count    DW  0
    limit    DW  0

.code
    LOAD  0
    STORE count
    LOAD  5
    STORE limit
L1:
    LOAD  1
    STORE t1
    LOAD  t1
    JZ    L2
    PUSH  count
    CALL  print
    LOAD  1
    STORE t2
    LOAD  1
    STORE count
    JMP   L1
L2:
    HALT
