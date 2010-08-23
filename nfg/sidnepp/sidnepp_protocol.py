#!/usr/bin/python

# interface for SIDN EPP 
#
# license: GPLv3
#
# copyright 2010, NFG Net Facilities Group BV, www.nfg.nl
#       
# Paul Stevens, paul@nfg.nl

from lxml import etree
import os.path

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

