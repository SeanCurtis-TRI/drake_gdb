import gdb
import re
import sys

class IdPrinter:
    TEMPLATE_RE = re.compile('^drake::geometry::Identifier<[\w+:]+::(\w+)Tag>$')
    def __init__(self, name, val, for_clion):
        self.name = name
        self.val = val
        self.for_clion = for_clion
    
    def to_string(self):
        i_val = self.val['value_']
        if (self.for_clion):
            return '%d' % (i_val)
        else: 
            return 'drake::geometry::Identifier<%sTag> (%d)' % (self.name, i_val)

def lookup_type(val, for_clion):
    raw_type = val.type.unqualified().strip_typedefs()

    constructor = None
    match = IdPrinter.TEMPLATE_RE.match(str(raw_type))
    if (match):
        constructor = IdPrinter(match.group(1), val, for_clion)

    return constructor

def register_printers(for_clion):
    '''Registers id printers with gdb.

    @param for_clion   If True, this is being invoked by a gdb instance in CLion.
    '''
    gdb.pretty_printers.append(lambda val: lookup_type(val, for_clion))
    
