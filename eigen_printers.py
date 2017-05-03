# -*- coding: utf-8 -*-
# This file is part of Eigen, a lightweight C++ template library
# for linear algebra.
#
# Copyright (C) 2009 Benjamin Schindler <bschindler@inf.ethz.ch>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Pretty printers for Eigen::Matrix
# This is still pretty basic as the python extension to gdb is still pretty basic. 
# It cannot handle complex eigen types and it doesn't support any of the other eigen types
# Such as quaternion or some other type. 
# This code supports fixed size as well as dynamic size matrices

# To use it:
#
# * Create a directory and put the file as well as an empty __init__.py in 
#   that directory.
# * Create a ~/.gdbinit file, that contains the following:
#      python
#      import sys
#      sys.path.insert(0, '/path/to/eigen/printer/directory')
#      from printers import register_eigen_printers
#      register_eigen_printers (None)
#      end

import gdb
import re
import itertools

class EigenAutoDiffScalarPrinter:
        def __init__(self, val, for_clion):
                # TODO: extract enough arguments for the autodiff scalar that it's declaration is clear.
                self.val = val
                self.for_clion = for_clion
                self.scalarValue = float(self.val['m_value'])

        class _iterator:
                VALUE = 0
                DERIVS = 1
                MAX_FIELDS = 2
                def __init__(self, value, derivs):
                        self.value = value
                        self.derivs = derivs
                        self.stage = self.VALUE

                def __next__(self):
                        result = None
                        if (self.stage == self.MAX_FIELDS):
                                raise StopIteration
                        elif (self.stage == self.VALUE):
                                result = ('value', self.value)
                        elif (self.stage == self.DERIVS):                                
                                result = ("derivatives", self.derivs)
                        self.stage += 1
                        return result

                def next(self):
                        return self.__next__()

                def __iter__(self):
                        return self

        def children(self):
                return self._iterator(self.scalarValue, self.val['m_derivatives'])

        def to_string(self):
                # TODO: Confirm that this is actually double -- although it's a safe assumption
                # TODO: Report the *size* of the derivatives vector.
                return "AutoDiffScalar<double>: {0:<14g}".format(self.scalarValue)

class EigenMatrixPrinter:
        "Print Eigen Matrix or Array of some kind"

        def __init__(self, variety, val, for_clion):
                "Extract all the necessary information"
                self.for_clion = for_clion
                if (for_clion):
                        self.children = lambda: self._iterator(self.rows, self.cols, self.data, self.rowMajor)

                # Save the variety (presumably "Matrix" or "Array") for later usage
                self.variety = variety
                
                # The gdb extension does not support value template arguments - need to extract them by hand
                template_params = self.get_template_parameters(val)
                if template_params[1] == '-0x00000000000000001' or template_params[1] == '-0x000000001' or template_params[1] == '-1':
                        self.rows = int(val['m_storage']['m_rows'])
                else:
                        self.rows = int(template_params[1])
                if template_params[2] == '-0x00000000000000001' or template_params[2] == '-0x000000001' or template_params[2] == '-1':
                        self.cols = int(val['m_storage']['m_cols'])
                else:
                        self.cols = int(template_params[2])
                self.options = 0 # default value
                if len(template_params) > 3:
                        self.options = template_params[3];
                
                self.rowMajor = (int(self.options) & 0x1)
                
                self.innerType = self.type.template_argument(0)
                
                self.val = val

                # Fixed size matrices have a struct as their storage, so we need to walk through this
                self.data = self.val['m_storage']['m_data']
                if self.data.type.code == gdb.TYPE_CODE_STRUCT:
                        self.data = self.data['array']
                        self.data = self.data.cast(self.innerType.pointer())

        class _iterator:
                def __init__ (self, rows, cols, dataPtr, rowMajor):
                        self.rows = rows
                        self.cols = cols
                        self.dataPtr = dataPtr
                        self.currentRow = 0
                        self.currentCol = 0
                        self.rowMajor = rowMajor
                        
                def __iter__ (self):
                        return self

                def next(self):
                        return self.__next__()  # Python 2.x compatibility

                def __next__(self):
                        
                        row = self.currentRow
                        col = self.currentCol
                        if self.rowMajor == 0:
                                if self.currentCol >= self.cols:
                                        raise StopIteration
                                        
                                self.currentRow = self.currentRow + 1
                                if self.currentRow >= self.rows:
                                        self.currentRow = 0
                                        self.currentCol = self.currentCol + 1
                        else:
                                if self.currentRow >= self.rows:
                                        raise StopIteration
                                        
                                self.currentCol = self.currentCol + 1
                                if self.currentCol >= self.cols:
                                        self.currentCol = 0
                                        self.currentRow = self.currentRow + 1
                                
                        item = self.dataPtr.dereference()
                        self.dataPtr = self.dataPtr + 1
                        if (self.cols == 1): #if it's a column vector
                                return ('[%d]' % (row,), item)
                        elif (self.rows == 1): #if it's a row vector
                                return ('[%d]' % (col,), item)
                        return ('[%d,%d]' % (row, col), item)

        def get_template_parameters(self, val):
                '''Handles the special case where the template parameters have nested template parameters.
                e.g., Eigen::Matrix<Eigen::AutoDifScalar<...>, 4, 4, 0, 4, 4>'''
                type = val.type
                if type.code == gdb.TYPE_CODE_REF:
                        type = type.target()
                self.type = type.unqualified().strip_typedefs()
                tag = self.type.tag
                parm_list_re = re.compile('<.*\>')
                parm_str = parm_list_re.findall(tag)[0][1:-1]

                # this *should* handle nested template types for the first parameter (the scalar value).
                param_re = re.compile('(?:[^<>]+<.*>\s*,)|(?:[^<>]+?(?:,|$))')
                template_params = []
                m = param_re.search(parm_str)
                while (m):
                        template_params.append(parm_str[m.pos:m.end()].strip(' ,'))
                        m = param_re.search(parm_str, m.end())
                return template_params

        def matString( self ):
                '''Produces a tab-indented, RXC printout of the matrix data.'''
                mat = ''
                ptr = self.data
                getFloat = float
                if (ptr.dereference().type.code != gdb.TYPE_CODE_FLT):
                        # assume autodiff
                        auto_diff_val = ptr.dereference()
                        getFloat = lambda x: float(x['m_value'])
                rows = [ [] for r in range(self.rows) ]
                widths = [0 for r in range(self.rows) ]
                if (self.rowMajor == 0 ):
                        for c in range(self.cols):
                                for r in range(self.rows):
                                        s = '{:.14g}'.format(getFloat(ptr.dereference()))
                                        widths[c] = max(widths[c], len(s))
                                        rows[r].append(s)
                                        ptr += 1
                else:
                        for r in range(self.rows):
                                for c in range(self.cols):
                                        s = '{:.14g}'.format(getFloat(ptr.dereference()))
                                        widths[c] = max(widths[c], len(s))
                                        rows[r].append(s)
                                        ptr += 1
                # compute column widths independently
                return '\n'.join(map(lambda row: '\t' + ''.join(map(lambda c: '{0:{1}}'.format(row[c], widths[c] + 1), range(len(row)))), rows))

        def get_major_label(self):
                '''Maps the row major boolean to a string for display'''
                if self.rowMajor:
                        return "RowMajor"
                else:
                        return "ColMajor"

        def get_prefix(self):
                '''Defines the display prefix -- can be overridden by derived classes'''
                return 'Eigen::%s<%s, %d, %d, %s>' % (self.variety, self.innerType, self.rows, self.cols, self.get_major_label())

        def to_string(self):
                '''Produces the string representation -- prefix, pointer, and matrix string representation.'''
                return self.get_prefix() + " (data ptr: %s)\n%s" % (self.data, self.matString())


class EigenTransformPrinter(EigenMatrixPrinter):
        def __init__(self, val, for_clion):
                EigenMatrixPrinter.__init__(self, "Transform", val["m_matrix"], for_clion)

                # The gdb extension does not support value template arguments - need to extract them by hand
                type = val.type
                if type.code == gdb.TYPE_CODE_REF:
                        type = type.target()
                type = type.unqualified().strip_typedefs()
                tag = type.tag
                regex = re.compile('\<.*\>')
                m = regex.findall(tag)[0][1:-1]
                template_params = m.split(',')
                self.mode = int(template_params[2])

        def get_mode_string(self):
                if (self.mode == 0):
                        return "Affine"
                elif (self.mode == 1):
                        return "AffineCompact"
                else:
                        return "Projective"

        def get_prefix(self):
                return 'Eigen::Transform<%s, %d, %s, %s>' % (self.innerType, self.rows - 1, self.get_mode_string(), self.get_major_label())
                

class EigenQuaternionPrinter:
        "Print an Eigen Quaternion"
        # The quaternion is four scalar values: this is the interpretation of the *order* of those values.
        elementNames = ['x', 'y', 'z', 'w']        
        def __init__(self, val, for_clion):
                "Extract all the necessary information"
                # The gdb extension does not support value template arguments - need to extract them by hand
                if (for_clion):
                        self.children = lambda: self._iterator(self.data)

                # I expect this will fail with AutoDiff
                type = val.type
                if type.code == gdb.TYPE_CODE_REF:
                        type = type.target()
                self.type = type.unqualified().strip_typedefs()
                self.innerType = self.type.template_argument(0)
                self.val = val
                
                # Quaternions have a struct as their storage, so we need to walk through this
                self.data = self.val['m_coeffs']['m_storage']['m_data']['array']
                self.data = self.data.cast(self.innerType.pointer())
                        
        class _iterator:
                def __init__ (self, dataPtr):
                        self.dataPtr = dataPtr
                        self.currentElement = 0
                        
                def __iter__ (self):
                        return self
        
                def next(self):
                        return self.__next__()  # Python 2.x compatibility

                def __next__(self):
                        element = self.currentElement
                        
                        if self.currentElement >= 4: #there are 4 elements in a quanternion
                                raise StopIteration
                        
                        self.currentElement = self.currentElement + 1
                        
                        item = self.dataPtr.dereference()
                        self.dataPtr = self.dataPtr + 1
                        return ('[%s]' % (EigenQuaternionPrinter.elementNames[element],), item)

        def quat_string(self):
                '''Produces a quaternion string of the form "value, <value, value, value>'''
                to_float = float
                ptr = self.data
                if (ptr.dereference().type.code != gdb.TYPE_CODE_FLT):
                        # assume autodiff
                        to_float = lambda x: float(x['m_value'])
                def getNextFloat(pointer):
                        val = to_float(pointer.dereference())
                        pointer += 1
                        return val
                values = [ getNextFloat(ptr) for x in range(4) ]
                q_values = dict(zip(self.elementNames, values))
                return '{w:.14g}, <{x:.14g}, {y:.14g}, {z:.14g}>'.format(**q_values)

        def to_string(self):
                return "Eigen::Quaternion<%s> (data ptr: %s)\n\t%s" % (self.innerType, self.data, self.quat_string())

def register_printers(for_clion):
        "Register eigen pretty-printers with objfile Obj"
        global pretty_printers_dict
        pretty_printers_dict[re.compile('^Eigen::AutoDiffScalar<.*>$')] = lambda val: EigenAutoDiffScalarPrinter(val, for_clion)
        pretty_printers_dict[re.compile('^Eigen::Quaternion<.*>$')] = lambda val: EigenQuaternionPrinter(val, for_clion)
        pretty_printers_dict[re.compile('^Eigen::Transform<.*>$')] = lambda val: EigenTransformPrinter(val, for_clion)
        pretty_printers_dict[re.compile('^Eigen::Matrix<.*>$')] = lambda val: EigenMatrixPrinter("Matrix", val, for_clion)
        pretty_printers_dict[re.compile('^Eigen::Array<.*>$')]  = lambda val: EigenMatrixPrinter("Array",  val, for_clion)
        gdb.pretty_printers.append(lambda val: lookup_function(val, for_clion))

def lookup_function(val, for_clion):
        "Look-up and return a pretty-printer that can print val."
        type = val.type
        orig = type
        
        if type.code == gdb.TYPE_CODE_REF:
                type = type.target()
        
        type = type.unqualified().strip_typedefs()
        typename = type.tag
        if typename == None:
                return None

        for function in pretty_printers_dict:
                if function.search(typename):
                        return pretty_printers_dict[function](val)
        
        return None

pretty_printers_dict = {}
