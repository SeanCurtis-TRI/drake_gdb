import gdb
import re
import sys

class IdPrinter:
    TEMPLATE_RE = re.compile('^drake::geometry::Identifier<[\w+:]+::(\w+)Tag>$')
    def __init__(self, name, val):
        #TODO: Use name when using command-line GDB but *not* in CLION
        self.name = name
        self.val = val
    
    def to_string(self):
        i_val = self.val['value_']
        return '%s: (%d)' % (self.name, i_val)

def lookup_type(val):
    raw_type = val.type.unqualified().strip_typedefs()

    constructor = None
    match = IdPrinter.TEMPLATE_RE.match(str(raw_type))
    if (match):
        name = '%s ID' % (match.group(1))
        constructor = IdPrinter(name, val)

    return constructor

def register_printers():
    gdb.pretty_printers.append(lookup_type)
    
