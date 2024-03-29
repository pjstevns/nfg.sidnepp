#!/usr/bin/python

# interface for SIDN EPP
#
# license: GPLv3
#
# copyright 2010-2013, NFG Net Facilities Group BV, www.nfg.nl
#
# Paul Stevens, paul@nfg.nl

import lxml.etree as ET
from lxml.builder import ElementMaker

EPP_NS = 'urn:ietf:params:xml:ns:epp-1.0'
HOST_NS = 'urn:ietf:params:xml:ns:host-1.0'
DOMAIN_NS = 'urn:ietf:params:xml:ns:domain-1.0'
CONTACT_NS = 'urn:ietf:params:xml:ns:contact-1.0'
SIDN_EXT_NS = 'http://rxsd.domain-registry.nl/sidn-ext-epp-1.0'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


class SIDNEppProtocol(object):

    EPP = "{%s}" % EPP_NS
    HOST = "{%s}" % HOST_NS
    DOMAIN = "{%s}" % DOMAIN_NS
    CONTACT = "{%s}" % CONTACT_NS
    SIDN_EXT = "{%s}" % SIDN_EXT_NS

    NSMAP = {
        'epp': EPP_NS,  # default namespace
        'host': HOST_NS,
        'domain': DOMAIN_NS,
        'contact': CONTACT_NS,
        'sidn-ext-epp': SIDN_EXT_NS,
        'xsi': XSI_NS,
    }

    def __init__(self):
        self.e_epp = ElementMaker(
            namespace=EPP_NS, nsmap={
                None: EPP_NS,
                'sidn-ext-epp': SIDN_EXT_NS,
            }
        )
        self.e_xsi = ElementMaker(
            namespace=EPP_NS, nsmap={
                None: EPP_NS,
                'xsi': XSI_NS,
                'domain': DOMAIN_NS,
            }
        )

        self.e_host = ElementMaker(namespace=HOST_NS, nsmap={'host': HOST_NS})
        self.e_domain = ElementMaker(namespace=DOMAIN_NS, nsmap={'domain':
                                                                 DOMAIN_NS})
        self.e_contact = ElementMaker(namespace=CONTACT_NS, nsmap={'contact':
                                                                   CONTACT_NS})
        self.e_sidn = ElementMaker(
            namespace=SIDN_EXT_NS,
            nsmap={
                'sidn-ext-epp': SIDN_EXT_NS
            }
        )

    def render(self, element):
        return ET.tostring(element, encoding="UTF-8",
                           pretty_print=True, standalone=False)

    def parse(self, message):
        try:
            return ET.fromstring(message, base_url=SIDN_EXT_NS)
        except ET.XMLSyntaxError:
            import traceback
            traceback.print_exc()
            print "Failed parsing:"
            print "------------------------------------------------------"
            print message
            print "------------------------------------------------------"

    def query(self, element, query):
        return element.xpath(query, namespaces=self.NSMAP)

    def readall(self, sock, size):
        got = ""
        while size > 0:
            buf = sock.recv(size)
            got += buf
            size -= len(buf)
        ##print "readall:", len(got),":", repr(got)
        return got

