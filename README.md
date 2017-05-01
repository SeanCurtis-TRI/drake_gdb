# GDB utilities for Drake

This project provides a number of debugging utilities for working with drake.

## Features

1. It can differentiate between being run in CLion and on the command line.
2. Provides convenient printouts of the "type safe" index types: `TypeSafeIndex` and `Identifier`.
  1. This assumes that they are used in the suggested method: e.g.,
  `using ThingId = Identifer<ThingTag>`. It will look for the ____Tag string to create display
   compact display name of the instantiated type.
3. Provides extended functionality for Eigen types beyond eigen's released functionality.
4. Handles `AutoDiff` types differently from `double` types.

## Install

1. Install the repository to some path: $DRAKE_GDB_ROOT$.
2. Create (if it doesn't already exist) the file `~/.gitinfo`
3. Insert the following lines:
```
python
import sys
sys.path.insert(0, $DRAKE_GDB_ROOT$)
import drake_gdb 
drake_gdb.register_printers(None)
end
```

Simply launch gdb and the pretty printers will be instantiated.

