import gc
# ... load certs ...
gc.collect() 
print(f"Free RAM after SSL setup: {gc.mem_free()} bytes")
print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc()))