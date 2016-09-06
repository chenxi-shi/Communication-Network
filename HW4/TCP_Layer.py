#!/usr/bin/python3
import IP_Layer
import random
from struct import pack, unpack
import socket

def checksum(msg):
	if (len(msg) % 2) != 0:
		msg += b'\x00'
	s = 0
	# loop taking 2 characters at a time
	for i in range(0, len(msg), 2):
		w = msg[i] + (msg[i + 1] << 8)
		s = s + w
	s = (s >> 16) + (s & 0xffff)
	s = s + (s >> 16)
	# complement and mask to 4 byte short
	s = ~s & 0xffff
	return s

class tcp_class():
	"""
	    0                   1                   2                   3
	0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|          Source Port          |       Destination Port        |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                        Sequence Number                        |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                    Acknowledgment Number                      |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|  Data |       |C|C|U|A|P|R|S|F|                               |
	| Offset| Reser |W|E|R|C|S|S|Y|I|            Window             |
	|       | ved   |R|C|G|K|H|T|N|N|                               |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|           Checksum            |         Urgent Pointer        |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                    Options                    |    Padding    |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                             data                              |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	"""
	def __init__(self, dst_port, src_ip, dst_ip, adv_wnd):
		# unassigned port numbers from IANA
		self.src_port = random.randrange(43124, 44320)
		self.dst_port = dst_port
		self.snd_seq = random.randrange(4294967295)
		self.relatv_seq = self.snd_seq
		self.relatv_ack = 0
		self.snd_ack = 0
		self.adv_wnd = adv_wnd
		self.tcp_urg_ptr = 0

		self.my_mss = 1460

		self.src_ip_n = socket.inet_aton(src_ip)
		self.dst_ip_n = socket.inet_aton(dst_ip)
		self.src_ip = src_ip
		self.dst_ip = dst_ip
		self.cwnd = 1
		self.cwnd = min(1000, self.cwnd)

		self.p = IP_Layer.ip_class(src_ip=self.src_ip, dst_ip=self.dst_ip)

		print('my port is {}'.format(self.src_port))
		print('my seq is {}'.format(self.snd_seq))

	def m_tcp_header(self, tcp_flag, tcp_opt=None, payload=None):
		self.tcp_chk = 0
		self.tcp_hl = 20
		self.tcp_offset_res = ((self.tcp_hl >> 2) << 4) + 0

		# tcp flags
		self.tcp_cwr = tcp_flag[0]  # sender sets to acknowledge receiver a receip of and reaction	to the ECN - Echoflag.
		self.tcp_ece = tcp_flag[1]  # sender support ECN (Explicit Congestion Notification)
		self.tcp_urg = tcp_flag[2]
		self.tcp_ack = tcp_flag[3]
		self.tcp_psh = tcp_flag[4]
		self.tcp_rst = tcp_flag[5]
		self.tcp_syn = tcp_flag[6]
		self.tcp_fin = tcp_flag[7]
		self.tcp_flags = self.tcp_fin + (self.tcp_syn << 1) + (self.tcp_rst << 2) + (self.tcp_psh << 3) + \
		                 (self.tcp_ack << 4) + (self.tcp_urg << 5) + (self.tcp_ece << 6) + (self.tcp_cwr << 7)
		self.tcp_opt = tcp_opt
		if self.tcp_opt:
			self.tcp_hl += len(self.tcp_opt)
			self.tcp_offset_res = ((self.tcp_hl >> 2) << 4) + 0
		# the ! in the pack format string means network order
		self.tcp_header = pack('!HHLLBBHHH', self.src_port, self.dst_port, self.snd_seq, self.snd_ack,
		                       self.tcp_offset_res, self.tcp_flags, self.adv_wnd, self.tcp_chk, self.tcp_urg_ptr)
		if self.tcp_opt:
			self.tcp_header += self.tcp_opt

		# pseudo header fields
		self.placeholder = 0
		self.protocol = socket.IPPROTO_TCP
		self.tcp_length = len(self.tcp_header)
		if payload:
			self.tcp_length += len(payload)

		self.psh = pack('!4s4sBBH', self.src_ip_n, self.dst_ip_n, self.placeholder, self.protocol, self.tcp_length)
		self.calcul_chks = self.psh + self.tcp_header
		if payload:
			self.calcul_chks += payload
		self.tcp_chk = checksum(self.calcul_chks)

		# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
		self.tcp_header = pack('!2H2L2BH', self.src_port, self.dst_port, self.snd_seq, self.snd_ack,
		                       self.tcp_offset_res, self.tcp_flags, self.adv_wnd) + \
		                  pack('H', self.tcp_chk) + pack('!H', self.tcp_urg_ptr)
		if self.tcp_opt:
			self.tcp_header += self.tcp_opt

	def m_tcp_segment(self, payload=None, resnd=False):
		"""
		generate a TCP Segment with payload (packed)
		0        1        2        3 byte
		+--------+--------+--------+--------+
		|           Source Address          |
		+--------+--------+--------+--------+
		|         Destination Address       |
		+--------+--------+--------+--------+
		|  zero  |  Proto |    TCP Length   |
		+--------+--------+--------+--------+
		pseudo header
		:param tcp_flag, payload, tcp_option
		:return: ip_packet
		"""
		self.resnd = resnd
		self.payload = payload
		if self.payload:
			self.nxt_snd_seq = self.snd_seq + len(self.payload)
			self.tcp_flags = (0, 1, 0, 1, 1, 0, 0, 0)
		else:
			self.nxt_snd_seq = self.snd_seq
			self.tcp_flags = (0, 1, 0, 1, 0, 0, 0, 0)

		tcp_class.m_tcp_header(self, tcp_flag=self.tcp_flags, payload=self.payload)
		if self.payload:
			self.tcp_segment = self.tcp_header + self.payload
		else:
			self.tcp_segment = self.tcp_header

		self.ip_datagram = self.p.ip_packet(self.tcp_segment)
		return self.ip_datagram

	def m_tcp_opt(self):
		"""
		create a tcp option part
		:return:
		"""
		self.tcp_nop = pack('!B', 1)
		return pack('!2BH', 2, 4, self.my_mss)

	def m_handshake_1(self, resnd=False):
		"""
		generate handshake one Segment
		:return: ip datagram
		"""
		self.resnd = resnd
		self.snd_opt = tcp_class.m_tcp_opt(self)
		self.tcp_flags = (0, 1, 0, 0, 0, 0, 1, 0)
		tcp_class.m_tcp_header(self, tcp_flag=self.tcp_flags, tcp_opt=self.snd_opt)

		self.ip_datagram = self.p.ip_packet(self.tcp_header)
		self.rcv_payload_len = 1
		self.nxt_snd_seq = self.snd_seq + 1

		return self.ip_datagram

	def m_handshake_3(self, resnd=False):
		"""
		generate handshake three Segment
		:return: ip datagram
		"""
		self.relatv_ack = self.rcv_seq
		self.snd_ack = self.rcv_seq + 1
		print('in handsh 3 seq {} ack {}'.format(self.snd_seq, self.snd_ack))
		self.resnd = resnd
		self.tcp_flags = (0, 1, 0, 1, 0, 0, 0, 0)
		tcp_class.m_tcp_header(self, tcp_flag=self.tcp_flags)

		self.ip_datagram = self.p.ip_packet(self.tcp_header)
		return self.ip_datagram

	def m_fin_handshake_2(self, resnd=False):
		"""
		generate finish handshake two Segment
		:return: ip datagram
		"""
		self.snd_ack += 1
		self.resnd = resnd
		self.tcp_flags = (0, 1, 0, 1, 0, 0, 0, 0)
		tcp_class.m_tcp_header(self, tcp_flag=self.tcp_flags)
		self.ip_datagram = self.p.ip_packet(self.tcp_header)
		self.nxt_snd_seq = self.snd_seq

		return self.ip_datagram

	def m_fin_handshake_3(self, resnd=False):
		"""
		generate finish handshake three Segment
		:return: ip datagram
		"""
		self.resnd = resnd
		self.tcp_flags = (0, 1, 0, 1, 0, 0, 0, 1)
		tcp_class.m_tcp_header(self, tcp_flag=self.tcp_flags)
		self.ip_datagram = self.p.ip_packet(self.tcp_header)
		self.nxt_snd_seq = self.snd_seq

		return self.ip_datagram

	def m_head_sniffer(self, rcv_segment, handshake=False):
		"""
		sniff tcp layer info
		:parameter segment (packed)
		:return data (packed)
		"""
		self.rcv_segment = rcv_segment
		self.rcv_header_raw = self.rcv_segment[:20]
		self.rcv_header = unpack('!HHLLBBHHH', self.rcv_header_raw)
		self.rcv_src_port = self.rcv_header[0]
		self.rcv_dst_port = self.rcv_header[1]
		self.rcv_seq = self.rcv_header[2]
		self.rcv_ack = self.rcv_header[3]
		self.rcv_data_offset = self.rcv_header[4] >> 4  # word length
		self.rcv_h_len = self.rcv_data_offset * 4  # byte length
		self.rcv_flags = self.rcv_header[5]
		self.rcv_wnd = self.rcv_header[6]
		self.rcv_chk = self.rcv_header[7]
		self.rcv_urg_ptr = self.rcv_header[8]

		if self.rcv_h_len is not 20:    # sniff tcp option part
			self.rcv_opt_raw = self.rcv_segment[20:self.rcv_h_len]

			self.pattern = 'B' * len(self.rcv_opt_raw)
			self.pattern = '!' + self.pattern
			self.rcv_opt = unpack(self.pattern, self.rcv_opt_raw)
			self.i = 0
			while True:
				if self.i < len(self.rcv_opt):
					if self.rcv_opt[self.i] == 1:
						self.i += 1
					else:
						if self.rcv_opt[self.i] == 4:
							self.tcp_sack = True
						elif self.rcv_opt[self.i] == 2:
							self.recv_mss = self.rcv_opt[self.i + 2] * 256 + self.rcv_opt[self.i + 3]
						elif self.rcv_opt[self.i] == 3:
							self.rcv_wdw_scl = self.rcv_opt[self.i + 2]
						elif self.rcv_opt[self.i] == 5:
							self.rcv_sack_len = self.rcv_opt[self.i + 1]
							for self.s in range(2, self.rcv_sack_len, 8):
								# there should be something but no time
								pass
						self.i += self.rcv_opt[self.i + 1]
				else:
					break

		self.rcv_segment_len = len(self.rcv_segment)

		if (self.src_port == self.rcv_dst_port) and (self.dst_port == self.rcv_src_port):

			if tcp_class.m_sniffer_checksum(self):

				if handshake:
					self.snd_ack = self.rcv_seq
					self.nxt_snd_ack = self.rcv_seq + 1
				else:
					self.rcv_payload_len = self.rcv_segment_len - self.rcv_h_len
					self.nxt_snd_ack = self.rcv_seq + self.rcv_payload_len

				if (self.rcv_seq == self.snd_ack) and (self.rcv_ack == self.nxt_snd_seq):
					self.snd_seq = self.nxt_snd_seq
					self.snd_ack = self.nxt_snd_ack

					self.cwnd += 1
					self.cwnd = min(1000, self.cwnd)
					if (self.rcv_flags & 1) is 1:   # FIN set
						return 999
					if self.rcv_payload_len == 0:    # all right, no payload
						return 112
					else:
						self.rcv_payload = self.rcv_segment[self.rcv_h_len:self.rcv_segment_len]#.decode(encoding='utf-8', errors='replace')
						return self.rcv_payload
				else:
					return 111
			else:
				return 111
		else:
			return 110

	def m_sniffer_checksum(self):
		# pseudo header fields
		self.rcv_src_ip_n = socket.inet_aton(self.dst_ip)
		self.rcv_dst_ip_n = socket.inet_aton(self.src_ip)
		self.rcv_protocol = socket.IPPROTO_TCP
		self.psh = pack('!4s4sBBH', self.rcv_src_ip_n, self.rcv_dst_ip_n, self.placeholder, self.rcv_protocol, self.rcv_segment_len)
		# tcp packet part, without checksum
		self.calcul_chks = self.psh + self.rcv_segment
		if checksum(self.calcul_chks) == 0:
			return True
		else:
			return False



