#!/usr/bin/env python3
import socket
from struct import pack, unpack

"""
The response to this query from A.ISI.EDU would be:

               +---------------------------------------------------+
    Header     | OPCODE=SQUERY, RESPONSE, AA                       |
               +---------------------------------------------------+
    Question   | QNAME=USC-ISIC.ARPA., QCLASS=IN, QTYPE=A          |
               +---------------------------------------------------+
    Answer     | USC-ISIC.ARPA. 86400 IN CNAME      C.ISI.EDU.     |
               | C.ISI.EDU.     86400 IN A          10.0.0.52      |
               +---------------------------------------------------+
    Authority  | <empty>                                           |
               +---------------------------------------------------+
    Additional | <empty>                                           |
               +---------------------------------------------------+

"""


def extract_domain_name(bytes_doc, i):
	domain_name = ''
	while bytes_doc[i] is not 0:
		# following is label
		label_len = bytes_doc[i]
		i += 1
		domain_name += bytes_doc[i:i + label_len].decode(errors='replace')
		domain_name += '.'
		i += label_len
	i += 1
	return domain_name, i


class dns_msg():
	"""
	DNS MESSAGES
	    +---------------------+
	    |        Header       | 12B
	    +---------------------+
	    |       Question      | (4+x)B the question for the name server
	    +---------------------+
	    |        Answer       | RRs answering the question
	    +---------------------+
	    |      Authority      | RRs pointing toward an authority
	    +---------------------+
	    |      Additional     | RRs holding additional information
	    +---------------------+
	"""

	snd_flg = b'\x81\x80'
	# TODO: get the num of dns_ans 1?2?
	dns_an = 1
	# TODO: figure out if the ns server is soa?
	dns_ns = 0
	dns_ar = 0
	dns_ttl = 120
	dns_dn = 'ns1.cs5700cdnproject.ccs.neu.edu'
	dns_cname = 'ec2-54-88-98-7.compute-1.amazonaws.com'

	def __init__(self, rcv_pkt):
		self.rcv_pkt = rcv_pkt

	def rcv_header(self):
		"""
		The header contains the following fields:
		                                    1  1  1  1  1  1
		      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                      ID                       |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                    QDCOUNT                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                    ANCOUNT                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                    NSCOUNT                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                    ARCOUNT                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		:return:
		"""
		[self.dns_id,
		 self.rcv_flg,
		 self.dns_qd,
		 self.rcv_an,
		 self.rcv_ns,
		 self.rcv_ar] = unpack('!H2s4H', self.rcv_pkt[:12])
		self.un_hdr_pkt = self.rcv_pkt[12:]

	def snd_header(self):
		self.qname_offset = 0
		self.snd_hdr = pack('!H2s4H',
		                    self.dns_id,
		                    dns_msg.snd_flg,
		                    self.dns_qd,
		                    dns_msg.dns_an,
		                    dns_msg.dns_ns,
		                    dns_msg.dns_ar)
		self.qname_offset += 12
		return self.snd_hdr

	def rcv_question(self):
		"""
		The question field:
		                                    1  1  1  1  1  1
		      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                                               |
		    /                     QNAME                     /
		    /                                               /
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                     QTYPE                     |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                     QCLASS                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		:return:
		"""
		i = 0
		[self.qname,
		 i] = extract_domain_name(self.un_hdr_pkt, i)
		# QNAME end
		[self.dns_type,
		 self.dns_class] = unpack('!2H', self.un_hdr_pkt[i:i + 4])
		i += 4

		self.snd_qst = self.un_hdr_pkt[:i]
		self.un_qst_pkt = self.un_hdr_pkt[i:]

	def rcv_answer(self):
		target = open('domain_db', 'w')
		i = 0
		# NAME starts
		if (self.un_qst_pkt[0] & 192) is 192:  # offset is used
			self.rcv_offset = unpack('!H', self.un_qst_pkt[:i + 2])[0] - 192
			i += 2
			self.rr_dn = extract_domain_name(self.rcv_pkt, self.rcv_offset)[0]
		else:  # offset is not used, low possibility
			[self.rr_dn,
			 i] = extract_domain_name(self.un_qst_pkt, i)
		target.write('{}\t'.format(self.rr_dn))
		# NAME ends
		# TYPE, CLASS, TTL start
		[self.rcv_type, self.rcv_class, self.rcv_ttl] = unpack('!2HL', self.un_qst_pkt[i:i + 8])
		i += 8
		target.write('{}\t{}\t'.format(self.rcv_type, self.rcv_class))
		# TYPE, CLASS, TTL end
		# Resource Domain starts
		[self.rcv_rd_len] = unpack('!H', self.un_qst_pkt[i:i + 2])
		i += 2
		if self.dns_type == 1:  # A
			target.write('{}\n'.format(socket.inet_ntoa(self.un_qst_pkt[i:i + self.rcv_rd_len])))
			i += self.rcv_rd_len
		elif self.dns_type == 2 or self.dns_type == 5:  # NS
			end_line = i + self.rcv_rd_len
			self.ns_dn = ''
			while i < end_line:
				if (self.un_qst_pkt[i] & 192) is 192:
					# offset is used
					self.rcv_offset = unpack('!H', self.un_qst_pkt[i:i + 2])[0] - 192
					i += 2
					self.ns_dn += extract_domain_name(self.rcv_pkt, self.rcv_offset)[0]
				else:
					[x, i] = extract_domain_name(self.un_qst_pkt, i)
					self.ns_dn += x
			target.write('{}\n'.format(self.ns_dn))
		# Resource Domain ends
		target.close()
		self.un_qst_pkt = self.un_qst_pkt[i:]

	def snd_answer(self, ip):
		"""
		The answer, authority, and additional sections all share the same format:
				                            1  1  1  1  1  1
		      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                                               |
		    /                                               /
		    /              NAME (may offset)                /
		    |                                               |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                      TYPE                     |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                     CLASS                     |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                      TTL                      |
		    |                                               |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    |                   RDLENGTH                    |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
		    /               RDATA (may offset)              /
		    /                                               /
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		When there is a RDATA, the NAME part is OFFSET
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		    | 1  1|                OFFSET                   |
		    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
		:return:
		"""
		self.ip_ans = ip
		self.snd_ans = pack('!3HL',
		                    self.qname_offset | 49152,
		                    self.dns_type,
		                    self.dns_class,
		                    dns_msg.dns_ttl)
		self.rd_len = 0
		# TODO: this rd_len come from choose result
		if self.dns_type == 1:  # A
			self.rd_len = 4
			self.snd_ans += pack('!H', self.rd_len) + socket.inet_aton(self.ip_ans)
		elif self.dns_type == 2:  # NS
			self.rd_len = len(dns_msg.dns_dn)
			self.snd_ans += pack('!H', self.rd_len)
			self.dns_dn_lst = dns_msg.dns_dn.split('.')
			for piece in self.dns_dn_lst:
				# TODO: here may use compression format
				self.snd_ans += pack('!B{}s'.format(len(piece)), len(piece), piece.encode(errors='replace'))
			self.snd_ans += pack('!B', 0)
		elif self.dns_type == 5:  # CNAME
			self.rd_len = len(dns_msg.dns_cname)
			self.snd_ans += pack('!H', self.rd_len)
			self.dns_dn_lst = dns_msg.dns_dn.split('.')
			for piece in self.dns_dn_lst:
				# TODO: here may use compression format
				self.snd_ans += pack('!B{}s'.format(len(piece)), len(piece), piece.encode(errors='replace'))
			self.snd_ans += pack('!B', 0)
		return self.snd_ans

	def debug_dns(self):
		print('ID: {}'.format(self.dns_id))
		print('Received Flags: {}'.format(self.rcv_flg))
		print('Query Count: {}'.format(self.dns_qd))
		if self.dns_qd > 0:
			self.debug_question()
		print('Answer Count: {}'.format(self.rcv_an))
		if self.rcv_an > 0:
			self.debug_answer()

	def debug_snd(self):
		print('ID: {}'.format(self.dns_id))
		print('Send Flags: {}'.format(dns_msg.snd_flg))
		print('Query Count: {}'.format(self.dns_qd))
		if self.dns_qd > 0:
			self.debug_question()
		print('Answer Count: {}'.format(dns_msg.dns_an))
		if dns_msg.dns_an > 0:
			self.debug_answer()

	def debug_question(self):
		print('\t[DEBUG]DNS QUESTION')
		print('\tRequest: {}', self.qname)
		print('\tType: {}\tClass: {}'.format(self.dns_type, self.dns_class))

	def debug_answer(self):
		print('\t[DEBUG]DNS ANSWER')
		print('\tQuery: {}'.format(self.qname_offset))
		print('\tType: {}\tClass: {}'.format(self.dns_type, self.dns_class))
		print('\tTTL: {}\tLength: {}'.format(dns_msg.dns_ttl, self.rd_len))
		print('\tIP answer: {}'.format(self.ip_ans))
