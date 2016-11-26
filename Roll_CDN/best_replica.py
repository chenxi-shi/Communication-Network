#!/usr/bin/env python3
__version__ = 'no thread'
"""
1st time client arrive:
    use distance calculator return
    &
    use http server ping and restore result
2nd time client arrive:
    use restored result
"""
import sys
import errno
import json
import socket
import time
import urllib.request
from math import radians, cos, sqrt

# import server_info

# (latitude, longitude)
replicas = {'ec2-54-85-32-37.compute-1.amazonaws.com':
                {'ip': '54.85.32.37', 'location': (39.018, -77.539), 'clients': set()},
            'ec2-54-193-70-31.us-west-1.compute.amazonaws.com':
                {'ip': '54.193.70.31', 'location': (37.3394, -121.895), 'clients': set()},
            'ec2-52-38-67-246.us-west-2.compute.amazonaws.com':
                {'ip': '52.38.67.246', 'location': (45.7788, -119.529), 'clients': set()},
            'ec2-52-51-20-200.eu-west-1.compute.amazonaws.com':
                {'ip': '52.51.20.200', 'location': (53.3331, -6.2489), 'clients': set()},
            'ec2-52-29-65-165.eu-central-1.compute.amazonaws.com':
                {'ip': '52.29.65.165', 'location': (50.1167, 8.6833), 'clients': set()},
            'ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com':
                {'ip': '52.196.70.227', 'location': (35.685, 139.7514), 'clients': set()},
            'ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com':
                {'ip': '54.169.117.213', 'location': (1.2931, 103.8558), 'clients': set()},
            'ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com':
                {'ip': '52.63.206.143', 'location': (-33.8615, 151.2055), 'clients': set()},
            'ec2-54-233-185-94.sa-east-1.compute.amazonaws.com':
                {'ip': '54.233.185.94', 'location': (-23.5475, -46.6361), 'clients': set()}
            }

client_ip = '129.10.116.51'
choosor_port = 58719
API_key = '19573919814e73623caec0d9e450d6228b2a42e40483e279af1e2e33979f64c8'


class socket_replica:
<<<<<<< HEAD
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, server_name, ping_port):
        self.ping_port = ping_port
        self.server_name = server_name
        self.sock.connect((self.server_name, self.ping_port))

    def send_client_ip(self, a_client_ip):
        # self.a_client_ip = socket.inet_aton(a_client_ip)
        self.a_client_ip = a_client_ip.encode()
        try:
            self.sock.sendall(self.a_client_ip)
        except socket.error as e:
            if isinstance(e.args, tuple):
                print("errno is {}".format(e))
                if e[0] == errno.EPIPE:
                    print("Detected remote disconnect")
                    self.sock.close()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.server_name, self.ping_port))
                    self.sock.sendall(self.a_client_ip)
                    time.sleep(0.1)
                else:
                    pass
            else:
                print("socket error (send)", e)

    def recv_rtt(self):
        try:
            self.RTT = self.sock.recv(256)
        except IOError as e:
            if e.errno == errno.EINTR:
                pass
            else:
                print("socket.error (recv) : %s" % e)
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server_name, self.ping_port))
                self.sock.sendall(self.a_client_ip)
                time.sleep(0.1)
        return self.RTT


class get_best_rpl:
    def __init__(self, ping_port):
        self.sock_dict = {}
        self.ping_port = ping_port + 1
        self.client_ip = None
        # TODO: how to set a socket dict
        for replica in replicas.keys():
            self.sock_dict[replica] = socket_replica()
            self.sock_dict[replica].connect(server_name=replica, ping_port=self.ping_port)

    def data_searcher(self, client_ip):
        # 2nd time client arrive:
        for info in replicas.values():
            if client_ip in info['clients']:
                return info['ip']
        return

    @staticmethod
    def client_loc(_client_ip):
        f = urllib.request.urlopen("http://api.ipinfodb.com/v3/ip-city/?key={}&ip={}".format(API_key, _client_ip))
        should_str = f.read().decode().split(';')
        return (float(should_str[-3]), float(should_str[-2]))

    @staticmethod
    def client_loc2(_client_ip):
        f = urllib.request.urlopen("http://geoip.nekudo.com/api/{}".format(_client_ip))
        should_str = json.loads(f.read().decode())
        return (should_str['location']['latitude'], should_str['location']['longitude'])

    @staticmethod
    def distance_calculator(_client_loc, replica_loc):
        """
        point(latitude, longitude)
        assume a small area (radius=100km) is flat
        arc length = r * included angle (radians)
        """
        x = _client_loc[1] - replica_loc[1]
        d_lon = min(x, 630 - x)  # longitude difference
        d_lat = _client_loc[0] - replica_loc[0]  # latitude difference

        m_lat = (_client_loc[0] + replica_loc[0]) / 2  # latitude midpoint

        L_lon = 6367000 * cos(radians(m_lat)) * radians(d_lon)  # 6367000m = earth radius
        L_lat = 6367000 * radians(d_lat)

        return sqrt(L_lat ** 2 + L_lon ** 2)

    @staticmethod
    def get_restore_min(replica_pair1=(), replica_pair2=()):
        if replica_pair1[1] < replica_pair2[1]:
            return replica_pair1
        else:
            return replica_pair2

    def loc_choosor(self, client_ip):
        """
        1st time client arrive:
        use distance calculator return
        apply map reduce for the best replica
        :param client_ip:
        :return:
        """

        self.client_ip = client_ip

        min_distance = 20000000
        min_distance_ip = ''
        client_loc = get_best_rpl.client_loc(self.client_ip)
        # get distances between client and each replica
        # map format: (replica_name, distance)
        dis_map = map(lambda replica: (replica[0], get_best_rpl.distance_calculator(client_loc, replica[1]['location'])),
                      replicas.items())

        best_replica_name, best_replica_dis = reduce(get_best_rpl.get_restore_min, dis_map)
        replicas[best_replica_name]['clients'].add(client_ip)

        print('Min Distance {}: replica {}'.format(best_replica_dis, best_replica_name))
        return replicas[best_replica_name]['ip']

    def ping_adder(self, client_ip):
        min_rtt = 36000
        min_rtt_host = 'host'
        print('\n[DEBUG] rtt_achiever')
        for host, one_sock in self.sock_dict.items():
            one_sock.send_client_ip(a_client_ip=client_ip)
            the_rtt = one_sock.recv_rtt()
            # TODO: make sure the format of response rtt
            the_rtt = float(the_rtt.decode())
            print('{}:{}'.format(host, the_rtt))
            if the_rtt < min_rtt:
                min_rtt_host = host
                min_rtt = the_rtt
        print('\nMIN_rtt_host: {}:{}'.format(min_rtt_host, min_rtt))
        replicas[min_rtt_host]['clients'].append(client_ip)
=======
	def __init__(self, sock=None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock

	def connect(self, server_name, ping_port):
		self.ping_port = ping_port
		self.server_name = server_name
		self.sock.connect((self.server_name, self.ping_port))

	def send_client_ip(self, a_client_ip):
		# self.a_client_ip = socket.inet_aton(a_client_ip)
		self.a_client_ip = a_client_ip.encode()  # to byte utf-8
		try:
			self.sock.sendall(self.a_client_ip)
		except socket.error as e:
			if isinstance(e.args, tuple):
				print("errno is {}".format(e))
				if e[0] == errno.EPIPE:
					print("Detected remote disconnect")
					self.sock.close()
					self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					self.sock.connect((self.server_name, self.ping_port))
					self.sock.sendall(self.a_client_ip)
					time.sleep(0.1)
				else:
					pass
			else:
				print("socket error (send)", e)

	def recv_rtt(self):
		try:
			self.RTT = self.sock.recv(256)
		except IOError as e:
			if e.errno == errno.EINTR:
				pass
			else:
				print("socket.error (recv) : %s" % e)
				self.sock.close()
				self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.sock.connect((self.server_name, self.ping_port))
				self.sock.sendall(self.a_client_ip)
				time.sleep(0.1)
		return self.RTT


class get_best_rpl:
	def __init__(self, ping_port):
		self.sock_dict = {}
		self.ping_port = ping_port + 1
		# TODO: how to set a socket dict
		for one_replica in replicas.keys():
			self.sock_dict[one_replica] = socket_replica()
			self.sock_dict[one_replica].connect(server_name=one_replica, ping_port=self.ping_port)

	def data_searcher(self, client_ip):
		# 2nd time client arrive:
		for info in replicas.values():
			if client_ip in info['clients']:
				return info['ip']
		return

	def loc_choosor(self, client_ip):
		# 1st time client arrive:
		# use distance calculator return
		self.client_ip = client_ip

		def client_loc(client_ip):
			f = urllib.request.urlopen("http://api.ipinfodb.com/v3/ip-city/?key={}&ip={}".format(API_key, client_ip))
			should_str = f.read().decode().split(';')
			return (float(should_str[-3]), float(should_str[-2]))

		def client_loc2(client_ip):
			f = urllib.request.urlopen("http://geoip.nekudo.com/api/{}".format(client_ip))
			should_str = json.loads(f.read().decode())
			return (should_str['location']['latitude'], should_str['location']['longitude'])

		def distance_calculator(client_loc, replica_loc):
			"""
			point(latitude, longitude)
			"""
			d_lat = client_loc[0] - replica_loc[0]
			d_lon = client_loc[1] - replica_loc[1]
			b = (client_loc[0] + replica_loc[0]) / 2
			L_lat = radians(d_lon) * 6367000 * cos(radians(b))
			L_lon = 6367000 * radians(d_lat)

			return sqrt(L_lat ** 2 + L_lon ** 2)

		min_distance = 20000000
		min_distance_ip = ''
		client_loc = client_loc(self.client_ip)
		for info in replicas.values():
			points_dis = distance_calculator(client_loc, info['location'])
			if points_dis < min_distance:
				min_distance_ip = info['ip']
				min_distance = points_dis
		print('Min Distance {}: replica {}'.format(min_distance_ip, min_distance))
		return min_distance_ip

	def ping_adder(self, client_ip):
		min_rtt = 36000
		min_rtt_host = 'host'
		print('\n[DEBUG] rtt_achiever')
		for host, one_sock in self.sock_dict.items():
			one_sock.send_client_ip(a_client_ip=client_ip)
			the_rtt = one_sock.recv_rtt()
			# TODO: make sure the format of response rtt
			the_rtt = float(the_rtt.decode())
			print('{}:{}'.format(host, the_rtt))
			if the_rtt < min_rtt:
				min_rtt_host = host
				min_rtt = the_rtt
		print('\nMIN_rtt_host: {}:{}'.format(min_rtt_host, min_rtt))
		replicas[min_rtt_host]['clients'].append(client_ip)
>>>>>>> origin/master


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(sys.argv)
        print('Usage: {} -p <port>'.format(sys.argv[0]))
        sys.exit()
    else:
        if sys.argv[1] == '-p':
            ping_port = int(sys.argv[2])
        else:
            print(sys.argv)
            print('Usage: {} -p <port>'.format(sys.argv[0]))
            sys.exit()
            # ccis_ip = '129.10.117.100'
            # client_Japan = '153.120.25.103'
            # client_Mexico = '148.245.38.39'
            # client_Germany = '85.114.141.191'
            # client_China = '182.254.153.54'
            # ping_port = ping_port + 1
            # print('HERE!!!!!!!!!!!!!!!!!!!!{}'.format(ping_port))
            # best = get_best_rpl(ping_port)
            # print('the min ip is {}'.format(best.loc_choosor(ccis_ip)))
            # best.ping_adder(ccis_ip)
            # print('the min ip is {}'.format(best.loc_choosor(client_Japan)))
            # best.ping_adder(client_Japan)
            # print('the min ip is {}'.format(best.loc_choosor(client_Mexico)))
            # best.ping_adder(client_Mexico)
            # print('the min ip is {}'.format(best.loc_choosor(client_Germany)))
            # best.ping_adder(client_Germany)
            # print('the min ip is {}'.format(best.loc_choosor(client_China)))
            # best.ping_adder(client_China)
