import os
import sys
import tempfile


class captured_stdout:
    def __init__(self):
        self.prevfd = None
        self.prev = None

    def __enter__(self):
        # F = tempfile.NamedTemporaryFile()
        F = open('D:/Users/addis/Desktop/testStuff.txt', 'w')

        # sys.stdout.flush()
        self.prevfd = os.dup(sys.stdout.fileno())
        os.dup2(F.fileno(), sys.stdout.fileno())
        # self.prev = sys.stdout
        # sys.stdout = os.fdopen(self.prevfd, "w")
        return F

    def __exit__(self, exc_type, exc_value, traceback):
        # sys.stdout.flush()
        # os.fsync(sys.stdout.fileno())
        # os.fsync(self.prevfd)

        # sys.stdout.close() # + implicit flush()
        # os.dup2(self.prevfd, 1)
        # sys.stdout = os.fdopen(self.prevfd, 'w') # Python writes to fd

        # sys.stdout.close()
        # os.dup2(self.prevfd, sys.stdout.fileno())
        # os.dup2(self.prevfd, self.prev.fileno())
        # sys.stdout = self.prev
        pass


##
## Example usage
##

## here is a hack to print directly to stdout
import ctypes
import ctypes.util
# Linux
# libc = ctypes.LibraryLoader(ctypes.CDLL).LoadLibrary("libc.so.6")

libc = ctypes.cdll.msvcrt

# libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
# c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')

# stdout = libc._fdopen(sys.stdout.fileno(), 'w')

def directfdprint(s):
    libc.printf(s)

# c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
#
# @contextmanager
# def stdout_redirector(stream):
#     # The original fd stdout points to. Usually 1 on POSIX systems.
#     original_stdout_fd = sys.stdout.fileno()
#
#     def _redirect_stdout(to_fd):
#         """Redirect stdout to the given file descriptor."""
#         # Flush the C-level buffer stdout
#         libc.fflush(c_stdout)

print("1 I'm printing from python before capture")
directfdprint(b"2 I'm printing from libc before capture\n")

with captured_stdout() as E:
    print("3 I'm printing from python in capture")
    directfdprint(b"4 I'm printing from libc in capture\n")
    E.flush()
    os.fsync(E.fileno())
    # E.close()
    sys.__stdout__.flush()
    # libc.fflush(stdout)
    # libc.fflush(None) # This makes it work
    # sys.stdout.flush()

print("5 I'm printing from python after capture")
directfdprint(b"6 I'm printing from libc after capture\n")

# print("Capture contains: " + repr(file(E.name).read()))
print("Capture contains: " + repr(open(E.name, 'r').read()))
