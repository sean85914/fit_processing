import os, struct
import fitparse
import argparse

# FIT protocol defintion: https://developer.garmin.com/fit/protocol/

def recover(fit_file, ignore=0):
	'''Recover broken FIT file.
	
	Parameters:
		fit_file (str): file name of FIT to recover
		ignore (int): how many bytes to ignore. Default is 0
	'''
	file_src = open(fit_file, 'rb')
	file_tgt = open(fit_file[:-4]+'_rec.fit', 'wb')
	
	wrote = b''
	
	# get broken file size
	file_src.seek(0, os.SEEK_END)
	file_size = file_src.tell()
	file_src.seek(0, os.SEEK_SET)
	
	# data size is broken
	broken_header = file_src.read(12)
	unpacked_data = struct.unpack('<2BHI4x', broken_header)
	header_size, protocol_ver_enc, profile_ver_enc, data_size = unpacked_data
	data_size = file_size - header_size - ignore
	fixed_header = struct.pack('<2BHI4s', header_size, protocol_ver_enc, profile_ver_enc, data_size, b'.FIT')
	file_tgt.write(fixed_header)
	file_tgt.write(struct.pack('<H', 0)) # dummy CRC
	wrote += (fixed_header + struct.pack('<H', 0))
	
	data = file_src.read()[2:-ignore] if ignore!=0 else file_src.read()[2:]
	file_tgt.write(data)
	wrote += data
	
	# compute CRC and write
	crc_value = 0
	crc_value = fitparse.records.Crc.calculate(wrote, 0)
	file_tgt.write(struct.pack('<H', crc_value))
	
	file_src.close()
	file_tgt.close()
	
# brute force
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('file', type=str, help='File to fix')
	args, _ = parser.parse_known_args()
	
	ignore = 0
	fixed_file = args.file[:-4] + '_rec.fit'
	while True:
		recover(args.file, ignore)
		fitfile = fitparse.FitFile(fixed_file, ignore)
		try:
			message = fitfile.messages
			print()
			break
		except Exception as e:
			ignore += 1
			print('\r{}'.format(ignore), end='')
		
	print('Recovered')