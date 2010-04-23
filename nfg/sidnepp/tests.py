#!/usr/bin/python


from sidnepp import SIDNEpp
from lxml import etree

import unittest

testuser='300271'
testpass='c2155d6292'

class testSidnEPP(unittest.TestCase):

    def setUp(self):
        self.o = SIDNEpp('testdrs.domain-registry.nl',700)

    def tearDown(self):
        self.o.logout()

    def testQuery(self):
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <command>
        <login>
        <clID>username</clID>
        <pw>password</pw>
        <options>
        <version>1.0</version>
        <lang>nl</lang>
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
        </epp>"""

        e = etree.fromstring(xml, self.o.parser)
        r1 = e.xpath('//epp:command', namespaces={'epp':"urn:ietf:params:xml:ns:epp-1.0"})
        self.failUnless(len(r1) == 1)
        r2 = self.o.query(e, "//epp:command")
        self.failUnless(r1 == r2)

    def testHello(self):
        s = self.o.hello()
        self.failUnless(len(s) > 0)
        r = self.o.query(s,'//epp:greeting')
        self.failUnless(len(r) > 0)

    def testLogin(self):
        s = self.o.login(testuser, testpass)
        r = self.o.query(s, '//epp:access')
        self.failUnless(len(r) > 0)

    def testLogout(self):
        self.o.login(testuser, testpass)
        s = self.o.logout()
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(r.get("code") == "1000")



if __name__ == '__main__':
     unittest.main()
