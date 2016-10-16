import socket
import ssl
import sys
import operator
import subprocess

chenxi = 'cs5700spring2016 HELLO ' + '001714204' + '\n'
print(chenxi)
def SoCo(serverPort, server, nuid, sslFlag):
	# Connection Info. It would be change when set Python Function
	# server = 'cs5700sp16.ccs.neu.edu'
	# serverPort = 27993
	# Get the Operators
	ops = { "+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.div }
    
	# Build Socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sslsock = ssl.wrap_socket(s, ssl_version = ssl.PROTOCOL_TLSv1)
	sslsock = ssl.wrap_socket(s)
	print(isinstance(sslFlag, int))
	
	if sslFlag == 1:
		if serverPort != 27994:
			print ("Warning: Wrong Server Port for SSL.")
			exit
		else:
			s = sslsock
	else:
		if serverPort != 27993:
			print ("Warning: Wrong Server Port.")
			exit
	try:
		# Try Connect
		s.connect((server, serverPort))
	except Exception as e:
		# Get Error
		print("something wrong with %s:%d. Exception is %s" % (server, serverPort, e))
	else:
		# Connect successful
		if sslFlag == 1:
			print ("SSL Connection Built")
		else:
			print("Connection Built")
		LSProj1 = 'cs5700spring2016 HELLO ' + nuid + '\n'
        
		# print >>sys.stderr, 'sending "%s"' % chenxi
		try:
			s.sendall(LSProj1)
		except Exception as e:
			print("something wrong with %s:%d. Exception is %s" % (server, serverPort, e))
		else:
			while 1:
				data = s.recv(256)
				if data.split()[1] == 'STATUS':
                    #print("the first respons: %s" %data)
					num1 = int(data.split()[2])
                    # print(isinstance(num1, int)) # is num1 int?
					num2 = int(data.split()[4])
					# print(isinstance(num2, int)) # is num2 int?
                    # print(isinstance(ops[data.split()[3]](num1, num2), int)) # is answer int?
					opAns = str(ops[data.split()[3]](num1, num2))
                    # print(isinstance(opAns, str)) # is answer string now?
					ans = 'cs5700spring2016 ' + opAns + '\n'
                    #print(ans)
					s.sendall(ans)
				elif data.split()[2] == 'BYE':
					print(data.split())
					break
	s.close()

#SoCo(27993, "cs5700sp16.ccs.neu.edu", "001714204")
