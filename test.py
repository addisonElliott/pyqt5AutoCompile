import os
import sys
import tempfile


class captured_stdout:
    def __init__(self):
        self.prevfd = None
        self.prev = None

    def __enter__(self):
        F = tempfile.NamedTemporaryFile()
        self.prevfd = os.dup(sys.stdout.fileno())
        os.dup2(F.fileno(), sys.stdout.fileno())
        self.prev = sys.stdout
        sys.stdout = os.fdopen(self.prevfd, "w")
        return F

    def __exit__(self, exc_type, exc_value, traceback):
        os.dup2(self.prevfd, self.prev.fileno())
        sys.stdout = self.prev


##
## Example usage
##

## here is a hack to print directly to stdout
import ctypes
# Linux
# libc = ctypes.LibraryLoader(ctypes.CDLL).LoadLibrary("libc.so.6")

libc = ctypes.cdll.msvcrt

def directfdprint(s):
    libc.printf(s)



print("I'm printing from python before capture")
directfdprint(b"I'm printing from libc before captrue\n")

with captured_stdout() as E:
    print("I'm printing from python in capture")
    directfdprint(b"I'm printing from libc in capture\n")

print("I'm printing from python after capture")
directfdprint(b"I'm printing from libc after captrue\n")

# print("Capture contains: " + repr(file(E.name).read()))
