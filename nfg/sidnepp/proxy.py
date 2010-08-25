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
from SocketServer import TCPServer, BaseRequestHandler

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..','..'))
from nfg.sidnepp.protocol import SIDNEppProtocol
from nfg.sidnepp.client import SIDNEppClient

class SIDNEppProxyHandler(BaseRequestHandler, SIDNEppProtocol):

    def _handle_hello(self, req):
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

    def _handle_login(self, r):
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <response>
        <result code="1000">
        <msg>The transaction was completed successfully.</msg>
        </result>
        <trID>
        <clTRID>1234</clTRID>
        <svTRID>1234</svTRID>
        </trID>
        </response>
        </epp>
        """
        self.write(xml)

    def _handle_logout(self, r):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <response>
        <result code="1500">
        <msg>You are now logged off.</msg>
        </result>
        <trID>
        <svTRID>1234</svTRID>
        </trID>
        </response>
        </epp>
        """
        self.write(xml)

    def handle(self):
        SIDNEppProtocol.__init__(self)
        # first read the incoming message from the client
        print "handle", self.client_address[0]
        while 1:
            try:
                req = self.read()
            except:
                break
            if self.query(req,'//epp:hello'):
                self._handle_hello(req)
            elif self.query(req,'//epp:login'):
                self._handle_login(req)
            elif self.query(req, '//epp:logout'):
                self._handle_logout(req)
            else:
                # write this message to the server
                print "send", etree.tostring(req)
                rep = self.server.client.write(etree.tostring(req))
                # post back the reply to the client
                print "received", etree.tostring(rep)
                self.write(etree.tostring(rep))

    def read(self):
        l = struct.unpack(">L", self.request.recv(4))[0]-4
        message = self.request.recv(l)
        return self.parse(message)

    def write(self, message):
        self.parse(message)
        self.request.send(struct.pack(">L", len(message)+4))
        self.request.send(message)


class SIDNEppProxy(TCPServer):
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
    client = None

    def __init__(self, (host, port), handler=None):
        if not handler: handler=SIDNEppProxyHandler
        TCPServer.__init__(self, (host, port), handler)

    def login(self, remote_host, remote_port, username, password):
        """ setup connection to remote EPP service 
        """
        self.client = SIDNEppClient(remote_host, remote_port, 
                                    username, password)
        return self.client._login

    def handle_timeout(self):
        print "proxy timeout"
        #raise IOError("request timeout")

def usage():
    print """

EPP Proxy server for SIDN 

usage:

proxy.py <options>

options:

    parameters for connecting to remote EPP service:

  --server=<epp server>
  --port=<epp server>
  --username=<epp username>
  --password=<epp password>

    parameters for setting up local proxy service:

  --address=<listen to address>
  --listen=<listen to port>

  """

if __name__ == '__main__':
    import getopt
    server = port = username = address = listen = None

    server    = 'testdrs.domain-registry.nl'
    port      = 700
    username  = '300271'
    password  = 'c2155d6292'

    address   = '127.0.0.1'
    listen    = 7000

    try:
        optlist, args = getopt.getopt(sys.argv[1:], [
            'server=', 
            'port=',
            'username=',
            'password=',
            'address=',
            'listen='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    for o,a in optlist:
        if o == '--server':
            server = a
        if o == '--port':
            port = int(a)
        elif o == '--username':
            username = a
        elif o == '--password':
            password = a
        elif o == '--address':
            address = a
        elif o == '--port':
            listen = int(a)

    if not (server and port and username and address and listen):
        usage()
        sys.exit(2)


    print "Starting SIDNEppProxy"
    proxy = SIDNEppProxy((address,listen))
    proxy.timeout=4
    proxy.login(server, port, username, password)
    print "succesfully logged into %s:%d" % (server, port)
    print "ready for clients on %s:%d" % (address, listen)
    proxy.serve_forever()
    print "parent child-exit"
    proxy.logout()
    print "parent done"
    sys.exit(0)

