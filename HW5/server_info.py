#!/usr/bin/env python3
"""
ec2-54-85-32-37.compute-1.amazonaws.com		N. Virginia
ec2-54-193-70-31.us-west-1.compute.amazonaws.com	N. California
ec2-52-38-67-246.us-west-2.compute.amazonaws.com	Oregon
ec2-52-51-20-200.eu-west-1.compute.amazonaws.com	Ireland   Ireland
ec2-52-29-65-165.eu-central-1.compute.amazonaws.com	Frankfurt 'Germany'
ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com	Tokyo  'Japan'
ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com	Singapore 'Singapore'
ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com	Sydney   'Australia'
ec2-54-233-185-94.sa-east-1.compute.amazonaws.com	Sao Paulo   'Brazil'
"""
"""
Private IP addresses:
192.168.0.0 - 192.168.255.255 (65,536 IP addresses)
(192\.168(\.(25[0-5]|2[0-5]\d|1\d{2}|\d{1,2})){2})|
172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses)
(172\.(1[6-9]|2\d|3[01])(\.(25[0-5]|2[0-5]\d|1\d{2}|\d{1,2})){2})|
10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)
(10(\.(25[0-5]|2[0-5]\d|1\d{2}|\d{1,2})){3})
127.0.0.1 ~ 127.255.255.254
"""
# (latitude, longitude)
replicas = {'ec2-54-85-32-37.compute-1.amazonaws.com':
	            {'ip': '54.85.32.37', 'location': (39.018, -77.539), 'clients': []},
            'ec2-54-193-70-31.us-west-1.compute.amazonaws.com':
	            {'ip': '54.193.70.31', 'location': (37.3394, -121.895), 'clients': []},
            'ec2-52-38-67-246.us-west-2.compute.amazonaws.com':
	            {'ip': '52.38.67.246', 'location': (45.7788, -119.529), 'clients': []},
            'ec2-52-51-20-200.eu-west-1.compute.amazonaws.com':
	            {'ip': '52.51.20.200', 'location': (53.3331, -6.2489), 'clients': []},
            'ec2-52-29-65-165.eu-central-1.compute.amazonaws.com':
	            {'ip': '52.29.65.165', 'location': (50.1167, 8.6833), 'clients': []},
            'ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com':
	            {'ip': '52.196.70.227', 'location': (35.685, 139.7514), 'clients': []},
            'ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com':
	            {'ip': '54.169.117.213', 'location': (1.2931, 103.8558), 'clients': []},
            'ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com':
	            {'ip': '52.63.206.143', 'location': (-33.8615, 151.2055), 'clients': []},
            'ec2-54-233-185-94.sa-east-1.compute.amazonaws.com':
	            {'ip': '54.233.185.94', 'location': (-23.5475, -46.6361), 'clients': []}}
