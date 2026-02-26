import sys
import zlib
with open(sys.argv[1],'rb') as file:
	data = zlib.decompress(file.read()).partion(b'\x00')[2]
	print(data.decode())
