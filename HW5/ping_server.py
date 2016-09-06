#!/usr/bin/env python
import random
import subprocess
import re
from SocketServer import BaseRequestHandler, TCPServer
import sys

target_ip = '129.10.116.51'


def pinger(target_ip):
	rtt_command = 'scamper -c \'ping -c 1\' -i {}'.format(target_ip)
	rtt_response = subprocess.check_output(rtt_command, shell=True)
	print('!!!!!!!!!!!!{}'.format(rtt_response))
	rtt_response = re.split(r'time=', rtt_response)[1].split(' ', 1)[0]
	if not rtt_response:
		rtt_response = 999999
	return rtt_response



class PingTCPHandler(BaseRequestHandler):
	def handle(self):
		self.target_ip = self.request.recv(1024)#.strip()
		print('TYPE!!!!!!{}',format(type(self.target_ip)))
		print('[DEBUG]Client address: {}'.format(self.target_ip))
		latency = pinger(target_ip=self.target_ip)
		print('[DEBUG]Latency: {}'.format(latency))
		self.request.sendall(latency)


class PingServer:
	def __init__(self, ping_port):
		self.ping_port = ping_port

	def start(self):
		print('HERE!!!!!!!!!!!!!!!!!{}'.format(self.ping_port))
		server = TCPServer(('', self.ping_port), PingTCPHandler)
		server.serve_forever()


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print(sys.argv)
		print('Usage: {} -p <port>'.format(sys.argv[0]))
		sys.exit()
	else:
		if sys.argv[1] == '-p':
			my_port = int(sys.argv[2])
		else:
			print(sys.argv)
			print('Usage: {} -p <port>'.format(sys.argv[0]))
			sys.exit()

	my_port = my_port + 1

	measure_server = PingServer(my_port)
	measure_server.start()
