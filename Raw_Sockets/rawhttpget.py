#!/usr/bin/python3
import Socket_Interface
import re
import sys


if __name__=='__main__':
	# url is entered from cmd line
	if len(sys.argv) != 2:
		print ('Usage: ./rawhttpget [URL]')
		sys.exit()
	URL = sys.argv[1]
print(URL)

#URL = 'http://david.choffnes.com/classes/cs4700sp16/2MB.log'
dst_port = 80

s = Socket_Interface.socket_class()

dst_netloc, dst_path= s.get_src_dst(URL)

dst_path_lst = re.split(r'/', dst_path)
file_name = dst_path_lst[-1]


def GET_msg(URL, dst_path, dst_netloc):
	GET_header = ('GET {} HTTP/1.1\n'.format(dst_path) +
	              'Host: {}\n'.format(dst_netloc) +
	              'Connection: Keep-Alive\n' +
	              'Referer: {}\n'.format(URL))
	return GET_header + '\n'

GET_it = GET_msg(URL, dst_path, dst_netloc).encode(encoding='utf-8', errors='replace')

s.connect()

whole_bytes = s.sockRecv(payload=GET_it)


target = open(file_name, 'wb')

if b'Content-Length: ' in whole_bytes:
	target.write(whole_bytes.split(b'Content-Type: text/x-log\r\n\r\n')[1])
elif b'Transfer-Encoding: chunked' in whole_bytes:
	file_split = re.split(b'\r\n[A-Fa-f0-9]{1,10}\r\n', whole_bytes)[1:-1]
	for each_chunk in file_split:
		target.write(each_chunk)

target.close()
exit()