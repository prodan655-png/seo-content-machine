# Suppress all print statements globally
import sys
import os

class SuppressOutput:
    def write(self, x): pass
    def flush(self): pass

# Only suppress if not in interactive mode
if not sys.stdout.isatty():
    sys.stdout = SuppressOutput()
    sys.stderr = SuppressOutput()
