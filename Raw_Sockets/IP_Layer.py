#!/usr/bin/python3
import Ethernet_Layer
import random
import socket
from struct import pack, unpack

def checksum(msg):
	if (len(msg) % 2) != 0:
		msg += b'0'
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

class ip_class():
	"""
	    0                   1                   2                   3
	0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|Version|  IHL  |Type of Service|          Total Length         |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|         Identification        |Flags|      Fragment Offset    |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|  Time to Live |    Protocol   |         Header Checksum       |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                       Source Address                          |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                    Destination Address                        |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	|                    Options                    |    Padding    |
	+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
	"""
	def __init__(self, src_ip, dst_ip):
		self.src_ip = src_ip
		self.dst_ip = dst_ip
		self.ip_ver = 4
		self.ip_ihl = 5  # 5 word(1 word 32bit)
		self.ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl
		self.ip_tos = int.from_bytes(b'\x68', 'little')  # 01101000
		self.ip_tot_len = 0  # kernel will fill the correct total length
		self.ip_id = random.randrange(10000, 30000)
		self.ip_flag = 2
		self.ip_flag_off = self.ip_flag << 13
		self.ip_ttl = 255
		self.ip_proto = socket.IPPROTO_TCP
		self.ip_h_chk = 0  # kernel will fill the correct checksum
		self.src_ip_n = socket.inet_aton(self.src_ip)
		self.dst_ip_n = socket.inet_aton(self.dst_ip)

		self.e = Ethernet_Layer.eth_class()


	def ip_packet(self, snd_segment):
		"""
		generate a ip datagram
		:parameter segment
		:return datagram
		"""
		self.ip_id += 1
		self.ip_header = pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.ip_tos, self.ip_tot_len, self.ip_id,
		                      self.ip_flag_off, self.ip_ttl, self.ip_proto, self.ip_h_chk, self.src_ip_n, self.dst_ip_n)

		self.snd_datagram = self.ip_header + snd_segment
		return self.snd_datagram

	def dup_ip_packet(self, snd_segment):
		"""
		generate a duplicate ip datagram
		:parameter segment
		:return datagram
		"""
		self.ip_header = pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.ip_tos, self.ip_tot_len, self.ip_id,
		                      self.ip_flag_off, self.ip_ttl, self.ip_proto, self.ip_h_chk, self.src_ip_n, self.dst_ip_n)
		self.snd_datagram = self.ip_header + snd_segment
		return self.snd_datagram

	def sniffer_checksum(self):
		# leave the 2B checksum part, when calculate checksum
		self.check_header = self.rcv_datagram[:10] + self.rcv_datagram[12:self.rcv_h_len]
		if checksum(self.check_header) == unpack('H', self.rcv_datagram[10:12])[0]:
			return True
		else:
			return False

	def head_sniffer(self, rcv_datagram):
		"""
		sniff ip layer info
		:parameter datagram
		:return tcp segment (packed) or False
		"""
		self.rcv_datagram = rcv_datagram
		self.rcv_header_raw = self.rcv_datagram[:20]
		self.rcv_header = unpack('!BBHHHBBH4s4s', self.rcv_header_raw)
		self.rcv_ihl = self.rcv_header[0] & 0x0F  # word length
		self.rcv_h_len = self.rcv_ihl * 4  # byte length
		self.rcv_tot_len = self.rcv_header[2]
		if self.rcv_h_len is not 20:
			self.rcv_opt = self.rcv_datagram[20:self.rcv_h_len]
		self.rcv_src_ip_a = socket.inet_ntoa(self.rcv_header[8])
		self.rcv_dst_ip_a = socket.inet_ntoa(self.rcv_header[9])
		self.rcv_ver = self.rcv_header[0] >> 4
		self.rcv_tos = self.rcv_header[1]
		self.rcv_id = self.rcv_header[3]
		self.rcv_flag_off = self.rcv_header[4]
		self.rcv_flag = self.rcv_flag_off >> 13
		self.rcv_off = self.rcv_flag_off & 0x7FF
		self.rcv_ttl = self.rcv_header[5]
		self.rcv_proto = self.rcv_header[6]
		self.rcv_h_chk = self.rcv_header[7]
		if self.rcv_h_len is not 20:
			self.rcv_opt = self.rcv_datagram[20:self.rcv_h_len]
		self.rcv_segment = self.rcv_datagram[self.rcv_h_len:self.rcv_tot_len]

		if (self.src_ip == self.rcv_dst_ip_a) and (self.dst_ip == self.rcv_src_ip_a):
			if ip_class.sniffer_checksum(self):
				return self.rcv_segment
			else:
				return 11
		else:
			return 10