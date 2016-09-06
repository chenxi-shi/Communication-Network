#!/usr/bin/python3
from struct import unpack

class eth_class():
	"""
	0        1        2        3        4        5  byte
	+--------+--------+--------+--------+--------+--------+
	|                   Destination MAC                   |
	+--------+--------+--------+--------+--------+--------+
	|                     Source MAC                      |
	+--------+--------+--------+--------+--------+--------+
	|    Ethertype    |           variable Data           |
	+--------+--------+--------+--------+--------+--------+
	"""


	def head_sniffer(self, rcv_frame):
		"""
		sniff ethernet layer info
		:parameter frame
		:return ip datagram (packed)
		"""
		self.rcv_frame = rcv_frame
		self.eth_header_raw = self.rcv_frame[:14]
		self.eth_header = unpack('!6s6sH', self.eth_header_raw)
		self.eth_src = self.eth_header[0]
		self.eth_dst = self.eth_header[1]
		self.eth_type_len = self.eth_header[2]
		self.eth_chk = self.rcv_frame[-4:]
		self.rcv_datagram = self.rcv_frame[14:]

		return self.rcv_datagram