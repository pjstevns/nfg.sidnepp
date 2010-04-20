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


class SIDNEpp:
    implements(IEpp)

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        schema_root = etree.XML(string.join(open('sidn-ext-epp-1.0.xsd','r').readlines(),''))
        schema = etree.XMLSchema(schema_root)
        self.parser = etree.XMLParser(schema=schema)
        self.connect()

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self._fd = ssl.wrap_socket(s)

    def write(self, message):
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
        return self._fd.read(need)

    def hello(self):
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
          <hello/>
        </epp>"""
        return self.write(xml)


    def login(self, login, password, newpassword=None, lang='NL'):
        pass

    def logout(self):
        pass

    def poll(self, ack=None):
        pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()

