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
import socket, struct, ssl, string
from lxml import etree
from StringIO import StringIO

STATE_INIT      = 0x01
STATE_CONNECTED = 0x02
STATE_LOGGEDIN  = 0x04

class SIDNEpp:
    implements(IEpp)

    _state = STATE_INIT

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        schema_root = etree.XML(string.join(open('sidn-ext-epp-1.0.xsd','r').readlines(),''))
        schema = etree.XMLSchema(schema_root)
        self.parser = etree.XMLParser(schema=schema)
        self.connect()
        self.hello()

    def connect(self):
        assert(self._state == STATE_INIT)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self._fd = ssl.wrap_socket(s)
        self._state = STATE_CONNECTED

    def write(self, message):
        assert(self._state > STATE_INIT)
        # validate
        etree.fromstring(message, self.parser)
        l = len(message)+4
        data = struct.pack(">L", l)
        self._fd.write(data)
        self._fd.write(message)
        return self._read()

    def _read(self):
        buf = self._fd.read(4)
        need = struct.unpack(">L", buf)
        need = need[0]-4
        s = self._fd.read(need)
        print s
        return etree.fromstring(s)

    def hello(self):
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
          <hello/>
        </epp>"""
        assert(self._state < STATE_LOGGEDIN)
        return self.write(xml)


    def login(self, login, password, newpassword=None, lang='NL'):
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
        res = self.write(xml)
        self._state = STATE_LOGGEDIN
        return res

    def logout(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="urn:ietf:params:xml:ns:epp-1.0
        epp-1.0.xsd">
        <command>
        <logout/>
        </command>
        </epp>
        """
        assert(self._state == STATE_LOGGEDIN)
        res = self.write(xml)
        self._state = STATE_CONNECTED
        return res
        

    def poll(self, ack=None):
        pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()

