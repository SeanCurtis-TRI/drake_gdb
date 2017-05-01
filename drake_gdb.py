import sys

# This is a *very* brittle mechanism for detecting clion vs. command-line gdb
# execution. CLion 2016.3.5 runs python version 2.7 and the command-line gdb
# runs version 3. In the future, if CLion upgrades, this will fail.
FOR_CLION = sys.version_info[0] == 2

import eigen_printers
import identifier
import type_safe_index

def register_printers():
    global FOR_CLION
    eigen_printers.register_printers(FOR_CLION)
    identifier.register_printers(FOR_CLION)
    type_safe_index.register_printers(FOR_CLION)
    
