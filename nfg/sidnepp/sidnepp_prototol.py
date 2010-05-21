#!/usr/bin/python

# interface for SIDN EPP 
#
# license: GPLv3
#
# copyright 2010, NFG Net Facilities Group BV, www.nfg.nl
#       
# Paul Stevens, paul@nfg.nl

from zope.interface import implements
from interfaces import IEpp
import socket, struct, ssl
from lxml import etree
import os.path

STATE_INIT      = 0x01
STATE_CONNECTED = 0x02
STATE_SESSION   = 0x04
STATE_LOGGEDIN  = 0x08

DEBUG=1

testserver = 'testdrs.domain-registry.nl'
testport   = 700
testuser   = '300271'
testpass   = 'c2155d6292'


def debug(msg=None):
    if msg and DEBUG: print msg

class SIDNEppProtocol(object):

    def __init__(self):
        xsd = os.path.join(os.path.dirname(__file__), 'xsd', 'sidn-ext-epp-1.0.xsd')
        self.parser = etree.XMLParser(schema=etree.XMLSchema(etree.parse(open(xsd,'r'))))

    def parse(self, message):
        return etree.fromstring(message, self.parser)

    def query(self, element, query):
        return element.xpath(query, 
                             namespaces={
                                 'epp': 'urn:ietf:params:xml:ns:epp-1.0',
                                 'host': 'urn:ietf:params:xml:ns:host-1.0',
                                 'domain': 'urn:ietf:params:xml:ns:domain-1.0',
                                 'contact':'urn:ietf:params:xml:ns:contact-1.0',
                                 'ext': 'urn:ietf:params:xml:ns:sidn-ext-epp-1.0',
                             })


class SIDNEppClient(SIDNEppProtocol):
    implements(IEpp)

    _connection_State = STATE_INIT
    
    # server frames
    _greeting = None
    _login = None

    def __init__(self, host=None, port=None, username=None, password=None,
                 ssl=True):
        super(SIDNEppClient, self).__init__()
        self.host = host
        self.port = port
        self.ssl = ssl
        self.connect()
        self._greeting = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(self.hello())
        if username and password:
            self._login = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                    etree.tostring(self.login(username, password))

    def connect(self):
        assert(self._connection_State == STATE_INIT) 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        if self.ssl:
            self._fd = ssl.wrap_socket(s)
        else:
            self._fd = s
        self._connection_State = STATE_CONNECTED

    def write(self, message):
        assert(self._connection_State > STATE_INIT)
        # validate
        self.parse(message)
        l = len(message)+4
        data = struct.pack(">L", l)
        self._fd.send(data)
        self._fd.send(message)
        return self.read()

    def read(self):
        buf = self._fd.recv(4)
        need = struct.unpack(">L", buf)
        need = need[0]-4
        return self.parse(self._fd.recv(need))

    def getState(self):
        return self._connection_State

# commands
    def hello(self):
        assert(self._connection_State == STATE_CONNECTED)
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
          <hello/>
        </epp>"""
        result = self.write(xml)
        assert(self.query(result,"//epp:greeting"))
        self._connection_State = STATE_SESSION
        return result

    def login(self, login, password, newpassword=None, lang='NL'):
        assert(self._connection_State == STATE_SESSION)
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <command>
        <login>
        <clID>%s</clID>
        <pw>%s</pw>
        <options>
        <version>1.0</version>
        <lang>%s</lang>
        </options>
        <svcs>
        <objURI>urn:ietf:params:xml:ns:contact-1.0</objURI>
        <objURI>urn:ietf:params:xml:ns:host-1.0</objURI>
        <objURI>urn:ietf:params:xml:ns:domain-1.0</objURI>
        <svcExtension>
        <extURI>urn:ietf:params:xml:ns:sidn-ext-epp-1.0</extURI>
        </svcExtension>
        </svcs>
        </login>
        </command>
        </epp>  
        """ % (login, password, lang)
        result = self.write(xml)
        r = self.query(result, "//epp:result")
        if not r:
            result = self.read()
            r = self.query(result, "//epp:result")
        self._connection_State = STATE_LOGGEDIN
        return result

    def logout(self):
        assert(self._connection_State == STATE_LOGGEDIN) 
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="urn:ietf:params:xml:ns:epp-1.0 epp-1.0.xsd">
        <command>
        <logout/>
        </command>
        </epp>
        """
        res = self.write(xml)
        self._fd.close()
        self._connection_State = STATE_INIT
        return res

    def poll(self, ack=None):
        assert(self._connection_State == STATE_LOGGEDIN) 
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?> 
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <command>
        <poll op="%s" %s/>
        </command>
        </epp>
        """
        op='req'
        msgid=''
        if ack:
            op='ack'
            msgid='msgID="%s"' % ack
        return self.write(xml % (op, msgid))

    def domain_check(self, domain):
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <command>
        <check>
        <domain:check xmlns:domain="urn:ietf:params:xml:ns:domain-1.0">
        <domain:name>%s</domain:name>
        </domain:check>
        </check>
        </command>
        </epp>
        """ % domain
        return self.write(xml)


from SocketServer import TCPServer, BaseRequestHandler

class SIDNEppProxyHandler(BaseRequestHandler, SIDNEppProtocol):

    def handle(self):
        SIDNEppProtocol.__init__(self)
        # first read the incoming message from the client
        req = self.read()
        print "handle", self.client_address[0], req
        if self.query(req,'//epp:hello'):
            xml = """<?xml version="1.0" encoding="UTF-8"?>
            <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
            <greeting>
            <svID>drs.domain-registry.nl</svID>
            <svDate>2008-12-03T14:00:17.372Z</svDate>
            <svcMenu>
            <version>1.0</version>
            <lang>en</lang>
            <lang>nl</lang>
            <objURI>urn:ietf:params:xml:ns:contact-1.0</objURI>
            <objURI>urn:ietf:params:xml:ns:domain-1.0</objURI>
            <objURI>urn:ietf:params:xml:ns:host-1.0</objURI>
            <svcExtension>
            <extURI>http://rxsd.domain-registry.nl/sidn-ext-epp-1.0</extURI>
            </svcExtension>
            </svcMenu>
            <dcp>
            <access>
            <all/>
            </access>
            <statement>
            <purpose>
            <admin/>
            <prov/>
            </purpose>
            <recipient>
            <ours/>
            <public/>
            </recipient>
            <retention>
            <stated/>
            </retention>
            </statement>
            </dcp>
            </greeting>
            </epp>
            """
            print "handle hello"
            self.write(xml)
        elif self.query(req,'//epp:login'):
            print "handle login"
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
            <response>
            <result code="1000">
            <msg>The transaction was completed successfully.</msg>
            </result>
            <trID>
            <clTRID></clTRID>
            <svTRID></svTRID>
            </trID>
            </response>
            </epp>
            """
            #self.write(self.server.server._login)
        elif self.query(req, '//epp:logout'):
            print "handle logout"
            xml = """<?xml version="1.0" encoding="UTF-8"?>
            <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
            <response>
            <result code="1500">
            <msg>You are now logged off.</msg>
            </result>
            <trID>
            <svTRID></svTRID>
            </trID>
            </response>
            </epp>
            """
            #self.write(xml)
        else:
            print "Oops", req
            # write this message to the server
            #rep = self.server.server.write(req)
            # post back the reply to the client
            #self.write(rep)

    def read(self):
        buf = self.request.recv(4)
        need = struct.unpack(">L", buf)
        need = need[0]-4
        return self.parse(self.request.recv(need))

    def write(self, message):
        self.parse(message)
        l = len(message)+4
        data = struct.pack(">L", l)
        self.request.send(data)
        debug("handler.write %d %d" % (id(self.request), id(message)))
        self.request.send(message)


class SIDNEppProxyServer(TCPServer):
    """
    >>> s = SIDNEppProxyServer(('127.0.0.1',7000))
    >>> s
    <__main__.SIDNEppProxyServer instance at 0x...>

    >>> s.timeout=.1
    >>> s.handle_request()
    Traceback (most recent call last):
    ...
    IOError: request timeout

    >>> s.login(testserver,testport,testuser,testpass)
    <Element {urn:ietf:params:xml:ns:epp-1.0}epp at ...>

    """
    allow_reuse_address = True

    # the remote EPP server connection
    server = None

    def __init__(self, (host, port), handler=None):
        if not handler: handler=SIDNEppProxyHandler
        TCPServer.__init__(self, (host, port), handler)

    def login(self, remote_host, remote_port, username, password):
        """ setup connection to remote EPP service 
        """
        self.server = SIDNEppClient(remote_host, 
                                    remote_port, 
                                    username,
                                    password)
        return self.server._login

    def handle_timeout(self):
        print "proxy timeout"
        #raise IOError("request timeout")


if __name__ == '__main__':
    import sys, time
    #import doctest
    #doctest.testmod(optionflags=doctest.ELLIPSIS)
    pid = os.fork()
    if pid:
        print "parent"
        proxy = SIDNEppProxyServer(('127.0.0.1',7000))
        #proxy.timeout=4
        #proxy.login(testserver, testport, testuser, testpass)
        while 1:
            print "parent handle_request"
            proxy.handle_request()
            check = os.waitpid(pid,os.WNOHANG)
            if check != (0,0): break
        print "parent child-exit"
        proxy.logout()
        print "parent done"
    else:
        print "child"
        SIDNEppClient('localhost', 7000, ssl=False).hello()
        print "login:", etree.tostring(SIDNEppClient('localhost', 7000, ssl=False).login('fakeusername','fakepassword'))
        #print "poll:", etree.tostring(client.poll())
        time.sleep(2)
        print "child done"
        sys.exit(0)

