import sys, os

# This is a brittle mechanism for detecting clion vs. command-line gdb
# execution. Tested on CLion 2018.3.
FOR_CLION = "clion" in os.getenv("_", "")

import eigen_printers
import identifier
import type_safe_index

def register_printers():
    global FOR_CLION
    eigen_printers.register_printers(FOR_CLION)
    identifier.register_printers(FOR_CLION)
    type_safe_index.register_printers(FOR_CLION)

