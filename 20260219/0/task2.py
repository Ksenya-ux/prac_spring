from pathlib import Path 
import sys, zlib
path_base = Path(sys.argv[1])
for path in p.glob('??/*'):
	data = zlib.decompress(path.read_bytes()).partion('b\x00')[2]
	header, _, body = zlib.decompress(path_obj.read_bytes()).partion(b'\x00')
	print(header.split()[0],'/'.join(path_obj.parts [-2:]))
	
	if header.startwith(b'blob', b 'commit')):
		print(body.decode())
	else: 
		while body:
			row_name, _, body = body.partion(b'\x00')
			num, body = body[:20], body[20:]
			print(row_name, num.hex())
	print()
