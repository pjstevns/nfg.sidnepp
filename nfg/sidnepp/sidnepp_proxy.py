#!/usr/bin/python

# interface for SIDN EPP
#
# license: GPLv3
#
# copyright 2010, NFG Net Facilities Group BV, www.nfg.nl
#
# Paul Stevens, paul@nfg.nl

import struct
from lxml import etree
import os.path

STATE_INIT = 0x01
STATE_CONNECTED = 0x02
STATE_SESSION = 0x04
STATE_LOGGEDIN = 0x08

DEBUG = 1

testserver = 'testdrs.domain-registry.nl'
testport = 700
testuser = '300271'
testpass = 'c2155d6292'

def debug(msg=None):
    if msg and DEBUG:
        print msg

from sidnepp_protocol import SIDNEppProtocol
from sidnepp_client import SIDNEppClient

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
            self.write(xml)
        elif self.query(req,'//epp:login'):
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
            self.write(xml)

        elif self.query(req, '//epp:logout'):
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
            self.write(xml)

        else:
            print "Oops", req
            # write this message to the server
            #rep = self.server.server.write(req)
            # post back the reply to the client
            #self.write(rep)

    def read(self):
        l = struct.unpack(">L", self.request.recv(4))[0]-4
        message = self.request.recv(l)
        return self.parse(message)

    def write(self, message):
        self.parse(message)
        self.request.send(struct.pack(">L", len(message)+4))
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
        self.server = SIDNEppClient(remote_host, remote_port, 
                                    username, password)
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

