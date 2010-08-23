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

from state import STATE_INIT, STATE_CONNECTED, STATE_SESSION, STATE_LOGGEDIN

from sidnepp_protocol import SIDNEppProtocol

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
        if r[0].attrib['code'] != '1000':
            raise Exception, "login failed. code was %s\nfull message:\n%s" % (
                r[0].attrib['code'], etree.tostring(r[0]))

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

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
