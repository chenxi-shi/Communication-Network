import socket
import errno
import time
import sys
import re
from multiprocessing.dummy import Pool as ThreadPool, Queue

import urlparse
from bs4 import BeautifulSoup

CookieC = ''
CookieS = ''
#username = '...'
#password = '...'
authorInfo = "..."
srcpage = 'http://cs5700sp16.ccs.neu.edu/fakebook/'
secret_flag = []
dictall = {}
start_time = time.time()
resocknum = 0
totaltry = 0
accessed = 0


class buildSock:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            self.sock = sock
            # return 1

    def connect(self, host, port):
        self.sock.connect((host, port))
        #return 1

    # no return trynum
    def sockSend(self, msg, location='cs5700sp16.ccs.neu.edu', port=80):
        #trynum = 0
        try:
            self.sock.sendall(msg)
            time.sleep(0.1)
        except socket.error as e:
            if isinstance(e.args, tuple):
                print("errno is %d" % e[0])
                if e[0] == errno.EPIPE:
                    print("Detected remote disconnect")
                    self.sockClose()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((location, port))
                    self.sock.sendall(msg)
                    time.sleep(1)
                else:
                    pass
            else:
                print("socket error (send)", e)

    # return recv, no trynum
    def sockRecv(self, msg, location='cs5700sp16.ccs.neu.edu', port=80):
        #trynum = 0
        buffer = ""
        data = ""
        while 1:
            try:
                data = self.sock.recv(256)
            except IOError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    print("socket.error (recv) : %s" % e)
                    self.sock.sockClose()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((location, port))
                    self.sock.sendall(msg)
                    time.sleep(1)
            else:
                if len(data) < 256:
                    if data == '0\r\n\r\n' or data == '':
                        self.sockClose()
                        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.sock.connect((location, port))
                        self.sock.sendall(msg)
                        time.sleep(2)
                    else:
                        buffer += data
                        break
                else:
                    buffer += data
        #print("!!!!!!!trynum is: ", trynum)
        return buffer#, trynum

    def sockClose(self):
        self.sock.close()
        #print("connection is closed by client")


def aGETmsg(authorInfo, dstpath, cookieC='', cookieS='', srcpage='', location='cs5700sp16.ccs.neu.edu'):
    Get1 = 'GET ' + dstpath + ' HTTP/1.1\r\n' + 'Host: ' + location + '\r\nConnection: Keep-Alive\r\n' + authorInfo
    if cookieC == '' and cookieS == '' and srcpage == '':
        pass
    else:
        Get1 += "\r\nReferer: " + srcpage + "\r\nCookie: csrftoken=" + cookieC + "; sessionid=" + cookieS
    return Get1 + '\r\n\r\n'


def getmiddleware(myrecv):
    soup = BeautifulSoup(myrecv, "html.parser")
    # print("find all hidden: ", soup.findAll(type="hidden"))
    middleware = soup.find(attrs={"name": "csrfmiddlewaretoken"}).get("value")
    # print(middleware)
    return middleware


def aPOSTmsg(authorInfo, URLpath, URLlocation, username, password, srcpage, middlew, cookieC, cookieS, resend=False):
    Form1 = "username={0}&password={1}&csrfmiddlewaretoken={2}&next=%2Ffakebook%2F".format(username, password, middlew)
    formlen = len(Form1)

    Postheader = "POST {0} HTTP/1.1\r\nAccept: text/html, application/xhtml+xml, image/jxr, */*\r\nReferer: {1}\r\n{2}\r\nContent-Type: application/x-www-form-urlencoded\r\nHost: {3}\r\nContent-Length: {4}\r\nConnection: Keep-Alive\r\nCookie: csrftoken={5}; sessionid={6}\r\n".format(
        URLpath, srcpage, authorInfo, URLlocation, formlen, cookieC, cookieS)
    if resend == False:
        return "{0}\r\n{1}".format(Postheader, Form1)
    else:
        return Postheader


def parseheader(doc, target):
    n = doc.count(target)
    splitdoc = doc.split(target, n)
    data = ''
    slist = [splitdoc[num + 1].split()[0] for num in range(n)]
    data = "".join(slist)
    if ';' in data:
        data = data[:-1]
    return data


def checkCookie(cookie, header, cookiestr):
    if cookiestr in header:
        return parseheader(header, cookiestr)
    else:
        return cookie


def getdestURL(doc, homepage='http://cs5700sp16.ccs.neu.edu/accounts/login/'):
    soup = BeautifulSoup(doc, "html.parser")
    if "HTTP/1.1 200" in doc:
        name = soup.find('input', {"name": "next"}).get('name')
        query = soup.find('input', {"name": "next"}).get("value")
        if query is u'':
            print("redirect is: ", homepage)
            return homepage
        else:
            print("!!!!!!!!!!!!!!query is:", query)
            return homepage + "?" + name + "=" + query
    elif "HTTP/1.1 302" in doc:
        URL = parseheader(doc, "Location: ")
        # print(URL)
        return URL
    elif "HTTP/1.1 400" in doc:
        return "HTTP/1.1 400"
    elif "HTTP/1.1 403" in doc:
        return "403 Forbidden"
    elif "HTTP/1.1 404" in doc:
        return "404 Not Found"
    elif "HTTP/1.1 500" in doc:
        return "500 Please retry"
    else:
        pass


# return URL list
def store1pageURL(myrecv):
    dict = []
    soup = BeautifulSoup(myrecv, "html.parser")
    for link in soup.findAll('a', href=True):
        a = str(link.get('href'))
        if "/fakebook/" in a:
            # make sure only restore /fakebook/ pages
            dict.append(a)
    return dict


#return flag or None
def checkFlag(myrecv):
    flag = re.findall(r"style=\"color:red\">(.+?)</h2>", myrecv)
    if flag:
        return flag


# return URLlist, flag
def AccessRestore(dstpath):
    global CookieC
    global CookieS
    global authorInfo
    global srcpage
    global secret_flag
    global dictall
    if len(secret_flag) >= 5:
        return
    sock = buildSock()
    sock.connect('cs5700sp16.ccs.neu.edu', 80)
    msg = aGETmsg(authorInfo, dstpath, CookieC, CookieS, srcpage)
    try:
        sock.sockSend(msg=msg)
        try:
            Recv = sock.sockRecv(msg=msg) # myrecv(0) and no tryed time(1)
        except IOError as e:
            print("socket.error : {0}".format(e))
    except IOError as e:
        print("IOError: {0}".format(e))
    else:
        URLlist = store1pageURL(Recv)
        flagstr = checkFlag(Recv)
        dictall[dstpath] = True
        sock.sockClose()
        #print("Thread finishes")
        return URLlist, flagstr

# return unaccessed pathes, change globals
def mp_handler(pathes):
    global dictall
    global secret_flag
    global pathednum
    global CookieC
    global CookieS
    global authorInfo
    global srcpage
    while len(secret_flag) < 5:
        newFalse = 0
        p = ThreadPool(10)
        print ("Parepare to access: ", len(pathes))
        try:
            couples = p.map(AccessRestore, pathes) # list of (URLlist, flagstr)
            pathednum += len(pathes)
        except IOError as e:
            print("IOerror : {0}".format(e))
        p.close()
        p.join()
        backpathes = []
        for couple in couples:
            if len(secret_flag) >= 5:
                return
            if couple is not None:
                for URL in couple[0]:
                    if URL not in dictall:
                        dictall[URL] = False
                        newFalse += 1
                        backpathes.append(URL)
                if couple[1] is not None:
                    if couple[1] not in secret_flag:
                        secret_flag.append(couple[1])

        print ("New False: ", newFalse)
        print ("accessed num: ", pathednum)
        print ("Whole(true and false) num: ", len(dictall))
        mp_handler(backpathes)

pathednum = 1
def mycrawler(username, password):
    global CookieC
    global CookieS
    global srcpage
    global authorInfo
    global accessed
    global dictall
    global secret_flag
    global pathednum
    #global retrynum
    homepage = 'http://cs5700sp16.ccs.neu.edu/accounts/login/?next=/fakebook/'	
    parsedURL = urlparse.urlparse(homepage)	
    URLscheme = parsedURL.scheme
    URLlocation = parsedURL.netloc
    URLpath = parsedURL.path
    CxQuery = parsedURL.query
    TCPPort = 80
    s = buildSock()
    s.connect(URLlocation, TCPPort)
    # prapare the 1st GET msg
    dstpath = URLpath + "?" + CxQuery
    try:
        # send the first GET for homepage
        msg = aGETmsg(authorInfo, dstpath)
        #print(msg)
        s.sockSend(msg = msg)
        # !!important info: Server will send whole msg,
        #     but it doesn't mean that socket.recv can get every thing onetime
        #     so, just let socket.recv receive more then one time
        
        myrecv = s.sockRecv(msg=msg) # return recv, no trynum
        #print(myrecv)
    except Exception as e:
        print("something wrong with recv. Exception is: %s" %e)
    else:        
    # prapare the POST msg
        # 1, Get the source page URL -- srcpage now it is still homepage
        # 2, Get the cookies from headers
        CookieC = checkCookie(CookieC, myrecv, "Set-Cookie: csrftoken=")
        CookieS = checkCookie(CookieS, myrecv, "Set-Cookie: sessionid=")
        # 3, Get the csrfmiddlewaretoken inside the HTML
        Cmiddleware = getmiddleware(myrecv)
        msg = aPOSTmsg(authorInfo, URLpath, URLlocation, username, password, srcpage, Cmiddleware, CookieC, CookieS)
        #print(msg)
        s.sockSend(msg=msg)
        myrecv = s.sockRecv(msg=msg) # return recv, no trynum
        #print(myrecv)
        adst = getdestURL(myrecv)
        if adst == ("403 Forbidden" or "404 Not Found"):
            msg = aPOSTmsg(authorInfo, URLpath, URLlocation, username, password, srcpage, Cmiddleware, CookieC, CookieS, True)
            #print(msg)
            s.sockSend(msg = msg)
            myrecv = s.sockRecv(msg=msg) # return recv, no trynum
            adst = getdestURL(myrecv)
    # prepare the 2nd GET msg	
        # the source page URL, it is still homepage
        #print(srcpage)
        # 2, Parse the next page URL path   
        parsedURL = urlparse.urlparse(adst)	
        URLpath = parsedURL.path # this is the destinatioin URL, then parse it get URLpath
        dstpath = URLpath
        # 3, Get the cookies from headers
        CookieC = checkCookie(CookieC, myrecv, "Set-Cookie: csrftoken=")
        CookieS = checkCookie(CookieS, myrecv, "Set-Cookie: sessionid=")
        msg = aGETmsg(authorInfo, dstpath, CookieC, CookieS, srcpage)
        #print(msg)
        try:
            # send the 2nd GET with new cookie
            s.sockSend(msg=msg)
        except Exception as e:
            print("something wrong with POST. Exception is: {0}".format(e))
        else:
            myrecv = s.sockRecv(msg=msg) # return recv, no trynum
            s.sockClose()
            srcpath = dstpath
            dictall[srcpath] = True
            pathednum += 1
            flag = checkFlag(myrecv)
            if flag is not None:
                if flag not in secret_flag:
                    secret_flag.append(flag)
            URLlist = store1pageURL(myrecv)
            for URL in URLlist:
                if URL not in dictall:
                    dictall[URL] = False
            # get my homepage
            #accessed = 1
            # Make the Pool of workers
            print (len(dictall))
            pathes = []
            pathednum = 1
            #while len(secret_flag) < 5:
            for key, value in dictall.iteritems():
                if value == False:
                    pathes.append(key)
            mp_handler(pathes)
            print(secret_flag)


mycrawler('001714204', 'GYSNIKX6')
print("--- {0} seconds ---".format(time.time() - start_time))
