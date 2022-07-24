Python Stub Hook C(++) Object

Introduction
============

I've created this little project for unit testing C(++) code using Python. If
you can produce an object file from C source(s) you're set! It can be used for
embedded code or (for example) sources from the Linux kernel.


Usage
=====

- Check out the sources from this project (download zip or git clone)
- Use the following template (GNU Make) Makefile, I'll be testing do_mounts.o from the Linux kernel so do a search & replace for do_mounts.
.. code-block:: Makefile
 
  CFLAGS=-fPIC -fprofile-arcs -ftest-coverage
  do_mounts.so: do_mounts.o stubs.o libhook.so
  	g++ -L. -lhook -shared -fPIC -Wl,-soname,do_mounts.so -o do_mounts.so -fprofile-arcs -ftest-coverage $^
  stubs.o: stubs.cpp
  	g++ -fPIC -c $<
  stubs.cpp: errors.txt generate.py
  	./generate.py errors.txt > stubs.cpp
  errors.txt: do_mounts.o
  	-g++ do_mounts.o 2> errors.txt
  libhook.so: libhook.cpp
  	g++ -shared -fPIC -Wl,-soname,libhook.so -o libhook.so libhook.cpp
  clean:
  	rm -f errors.txt do_mounts.so do_mounts.o stubs.cpp stubs.o libhook.so
 
 
- Run make, it will generate do_mounts.so by generating stubs.cpp from the gcc linker errors when linking do_mounts.o.
- Write your Python test script, you can use the following boiler plate code:
.. code-block:: Python
 
  #!/usr/bin/python3
  import ctypes
  import json
  import sys

  with open('stubs.cpp') as f:
      for line in f:
          if line.startswith('/* pycallbacks ='):
              pycallbacks = json.loads(line[17:-3])

  libhook = ctypes.CDLL('./libhook.so')

  callback = ctypes.CFUNCTYPE(ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong))
  registercallback = libhook.registercallback
  registercallback.argtypes = [ctypes.c_longlong, callback, ctypes.c_int]

  cbs = []
  def generatefn(name):
      def fn(a):
          nonlocal name
          print(name)
          return 0
      return fn

  for cb, i in pycallbacks.items():
      cbs.append(callback(generatefn(cb)))
      registercallback(i, cbs[-1], 0)

  buffers = []

  def x_alloc_page(a):
      b = ctypes.create_string_buffer(100000)
      buffers.append(b)
      return ctypes.addressof(b)

  def x_page_address(a):
      return a[0]

  def panic(a):
      print('panic:', ctypes.cast(a[0], ctypes.c_char_p).value)
      sys.exit()
      return 0

  cbs.append(callback(x_alloc_page))
  registercallback(pycallbacks["x_alloc_page"], cbs[-1], 2)
  cbs.append(callback(x_page_address))
  registercallback(pycallbacks["x_page_address"], cbs[-1], 1)
  cbs.append(callback(panic))
  registercallback(pycallbacks["panic"], cbs[-1], 1)

  do_mounts = ctypes.CDLL('./do_mounts.so')
  prepare_namespace = do_mounts.prepare_namespace
  prepare_namespace()
 
 
- Run the python script (./domounts.py) and watch the output.
