import gc
print("Free RAM:", gc.mem_free(), "bytes")

import os
fs = os.statvfs('/')
print("Free Flash:", fs[0] * fs[3], "bytes")