#!/usr/bin/python

# interface for SIDN EPP
#
# license: GPLv3
#
# copyright 2010-2013, NFG Net Facilities Group BV, www.nfg.nl
#
# Paul Stevens, paul@nfg.nl

import struct
from lxml import etree
from SocketServer import TCPServer, BaseRequestHandler

import sys
import signal
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from nfg.sidnepp.protocol import SIDNEppProtocol
from nfg.sidnepp.client import SIDNEppClient

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)


def handle_pdb(sig, frame):
    import pdb
    pdb.Pdb().set_trace(frame)


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
        <access><all/></access>
        <statement><purpose><admin/><prov/></purpose>
        <recipient><ours/><public/></recipient>
        <retention><stated/></retention>
        </statement>
        </dcp>
        </greeting>
        </epp>
        """
        self.write(xml)

    def _handle_login(self, r):
        e = self.e_epp
        x = e.epp(
            e.response(
                e.result(
                    e.msg('The transaction was completed successfully.'),
                    code='1000'
                ),
                e.trID(
                    e.clTRID('1234'),
                    e.svTRID('1234')
                )
            )
        )
        self.write(x)

    def _handle_logout(self, r):
        e = self.e_epp
        x = e.epp(
            e.response(
                e.result(e.msg('You are now logged off.'), code='1500'),
                e.trID(
                    e.svTRID('1234')
                )
            )
        )
        self.write(x)

    def handle(self):
        SIDNEppProtocol.__init__(self)
        # first read the incoming message from the client
        log.debug("handle %s" % self.client_address[0])
        while 1:
            try:
                req = self.read()
            except:  # client hung up
                break
            if self.query(req, '//epp:hello'):
                self._handle_hello(req)
            elif self.query(req, '//epp:login'):
                self._handle_login(req)
            elif self.query(req, '//epp:logout'):
                self._handle_logout(req)
                break
            else:
                # write this message to the server
                # and post back the reply to the client
                self.write(self.server.client.write(req))

    def read(self):
        log.debug("reading...")
        buf = self.readall(self.request, 4)
        buf = self.readall(self.request, struct.unpack(">L", buf)[0] - 4)
        log.debug("reading done.")
        msg = self.parse(buf)
        log.debug("read %s" % self.render(msg))
        return msg

    def write(self, message):
        if type(message) == etree._Element:
            message = self.render(message)
        else:
            self.parse(message)
        log.debug("write %s" % message)
        self.request.sendall(struct.pack(">L", len(message) + 4))
        self.request.sendall(message)


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
        signal.signal(signal.SIGUSR1, handle_pdb)
        if not handler:
            handler = SIDNEppProxyHandler
        TCPServer.__init__(self, (host, port), handler)

    def login(self, remote_host, remote_port, username, password):
        """setup connection to remote EPP service
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

  -s <addr> --server=<epp server>           default: testdrs.domain-registry.nl
  -p <port> --port=<epp server>             default: 700
  -u <username> --username=<epp username>
  -w <password> --password=<epp password>

    parameters for setting up local proxy service:

  -a --address=<listen to address>          default: localhost
  -l --listen=<listen to port>              default: 7000

  """

if __name__ == '__main__':
    import getopt
    server = port = username = address = listen = None

    server = 'testdrs.domain-registry.nl'
    port = 700
    username = False
    password = False

    address = '127.0.0.1'
    listen = 7000

    try:
        optlist, args = getopt.getopt(sys.argv[1:], "s:p:u:w:a:l", [
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

    for o, a in optlist:
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
        elif o == '--listen':
            listen = int(a)

    if not (username and password):
        usage()
        sys.exit(2)

    print "Starting SIDNEppProxy"
    proxy = SIDNEppProxy((address, listen))
    proxy.timeout = 4
    proxy.login(server, port, username, password)
    print "Connected to: %s:%d" % (server, port)
    print "Listen on: %s:%d" % (address, listen)
    proxy.serve_forever()
    proxy.logout()
    print "parent done"
    sys.exit(0)

