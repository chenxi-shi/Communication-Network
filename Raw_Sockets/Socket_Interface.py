#!/usr/bin/python3
import TCP_Layer
import IP_Layer
import Ethernet_Layer
import socket
from urllib.parse import urlparse
import sys
import time

def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]


class socket_class():
	def __init__(self, snd_sock=None, rcv_sock=None):
		self.adv_wnd = 1024
		self.dst_port = 80
		self.c_wnd = 1
		self.max_cwnd = 1000
		self.c_wnd = min(self.c_wnd, self.max_cwnd)
		if snd_sock is None:
			try:
				self.snd_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
			except OSError as sock_error:
				print(sock_error)
				sys.exit(sock_error.errno)
		else:
			self.snd_sock = snd_sock
		if rcv_sock is None:
			try:
				self.rcv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))
			except OSError as sock_error:
				print(sock_error)
				sys.exit(sock_error.errno)
		else:
			self.rcv_sock = rcv_sock

		self.buffer = bytearray(8192)
		self.data_buffer = bytearray()

	def get_src_dst(self, URL):
		self.parsedURL = urlparse(URL)
		self.dst_netloc = self.parsedURL.netloc
		self.dst_path = self.parsedURL.path
		self.dst_ip = socket.gethostbyname(self.dst_netloc)
		self.src_ip = get_ip_address()
		self.t = TCP_Layer.tcp_class(dst_port=self.dst_port, src_ip=self.src_ip, dst_ip=self.dst_ip, adv_wnd=self.adv_wnd)
		self.p = IP_Layer.ip_class(src_ip=self.src_ip, dst_ip=self.dst_ip)
		self.e = Ethernet_Layer.eth_class()
		return self.dst_netloc, self.dst_path

	def connect(self):
		"""
		3 handshake
		:parameter
		:return
		"""
		self.snd_sock.sendto(self.t.m_handshake_1(), (self.dst_ip, self.dst_port))
		self.start_time = time.time()
		while True:
			if (time.time() - self.start_time) < 60:
				self.rcv_frame_len, self.sender = self.rcv_sock.recvfrom_into(buffer=self.buffer, nbytes=4608)

				self.rcv_datagram = self.e.head_sniffer(rcv_frame=self.buffer)
				if self.rcv_datagram:
					self.rcv_segment = self.p.head_sniffer(rcv_datagram=self.rcv_datagram)
					if self.rcv_segment == 10:  # IP WRONG, receive
						continue
					elif self.rcv_segment == 11:  # checksum WRONG, resend
						pass
					else:
						self.rcv_payload = self.t.m_head_sniffer(rcv_segment=self.rcv_segment, handshake=True)
						if self.rcv_payload == 110:  # port WRONG, receive
							continue
						elif self.rcv_payload == 111:  # tcp checksum or seq WRONG, resend
							pass
						else:
							self.c_wnd += 1
							self.c_wnd = min(self.c_wnd, self.max_cwnd)
							break
			else:
				print('TIMEOUT. The downloading of webpage has been gave up.')
				exit()
			self.snd_sock.sendto(self.t.m_handshake_1(resnd=True), (self.dst_ip, self.dst_port))
			self.start_time = time.time()

		self.snd_sock.sendto(self.t.m_handshake_3(), (self.dst_ip, self.dst_port))
		self.start_time = time.time()


	def sock_rebuild(self):
		self.snd_sock.close()
		self.rcv_sock.close()
		time.sleep(0.1)
		self.snd_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
		self.rcv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))
		socket_class.connect(self)


	def sockRecv(self, payload):
		self.snd_payload = payload
		self.fin = False
		while not self.fin:
			self.snd_sock.sendto(self.t.m_tcp_segment(payload=self.snd_payload), (self.dst_ip, self.dst_port))
			self.start_time = time.time()

			while True:
				if (time.time() - self.start_time) < 60:
					self.rcv_frame_len, self.sender = self.rcv_sock.recvfrom_into(buffer=self.buffer, nbytes=2048)

					self.rcv_datagram = self.e.head_sniffer(rcv_frame=self.buffer)
					if self.rcv_datagram:
						self.rcv_segment = self.p.head_sniffer(rcv_datagram=self.rcv_datagram)
						if self.rcv_segment == 10:  # IP WRONG, receive
							continue
						elif self.rcv_segment == 11:  # IP checksum WRONG, resend
							pass
						else:
							self.rcv_payload = self.t.m_head_sniffer(rcv_segment=self.rcv_segment)
							if self.rcv_payload == 110:  # port WRONG, receive
								continue
							elif self.rcv_payload == 111:  # received checksum or seq or ack # WRONG! resend
								pass
							elif self.rcv_payload == 999:
								self.fin = True
								socket_class.close(self)
								break
							elif self.rcv_payload == 112:  # receive right but no data, receive
								self.c_wnd += 1
								self.c_wnd = min(self.c_wnd, self.max_cwnd)
								continue
							else:
								self.data_buffer.extend(self.rcv_payload)  # receive right data, ack
								self.c_wnd += 1
								self.c_wnd = min(self.c_wnd, self.max_cwnd)
								break
				else:
					print('TIMEOUT. The downloading of webpage has been gave up.')
					exit()
				self.snd_sock.sendto(self.t.m_tcp_segment(payload=self.snd_payload, resnd=True), (self.dst_ip, self.dst_port))
				#self.snd_sock.sendto(self.t.tcp_segment(payload=self.snd_payload), (self.dst_ip, self.dst_port))
				self.start_time = time.time()

			self.snd_payload = None

		return self.data_buffer


	def close(self):
		print('In the end the cwnd is {}'.format(self.c_wnd+1))
		self.snd_sock.sendto(self.t.m_fin_handshake_2(), (self.dst_ip, self.dst_port))
		self.snd_sock.sendto(self.t.m_fin_handshake_3(), (self.dst_ip, self.dst_port))


