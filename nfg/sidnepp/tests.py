#!/usr/bin/python


from lxml import etree
import unittest

from sidnepp_protocol import SIDNEppProtocol
from sidnepp_client import SIDNEppClient

testserver = 'testdrs.domain-registry.nl'
testport   = 700
testuser   = '300271'
testpass   = 'c2155d6292'

class testSidnEppProtocol(unittest.TestCase):

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


    def setUp(self):
        self.o = SIDNEppProtocol()

#    def tearDown(self):
#        try:
#            self.o.logout()
#        except AssertionError: 
#            pass

    def test_parse(self):
        e = self.o.parse(self.xml)
        print e

    def testQuery(self):
        e = self.o.parse(self.xml)
        r1 = e.xpath('//epp:command', namespaces={'epp':"urn:ietf:params:xml:ns:epp-1.0"})
        self.failUnless(len(r1) == 1)
        r2 = self.o.query(e, "//epp:command")
        self.failUnless(r1 == r2)
        r3 = self.o.query(e,"//epp:login")
        self.failUnless(type(r3) == type(r2))


class testSIDNEppClient(unittest.TestCase):

    def setUp(self):
        self.o = SIDNEppClient(testserver,testport)

    def testLogin(self):
        s = self.o.login(testuser, testpass)
        r = self.o.query(s, '//epp:result')
        self.failUnless(len(r) > 0)

#    def testLogout(self):
#        s = self.o.login(testuser, testpass)
#        r = self.o.query(s, '//epp:access')[0]
#        s = self.o.logout()
#        r = self.o.query(s, '//epp:result')[0]
#        self.failUnless(r.get("code") == "1000")
#
    def testPoll(self):
        s = self.o.login(testuser, testpass)
        print etree.tostring(s)
        s = self.o.poll()
        print etree.tostring(s)

#    def testDomainCheck(self):
#        self.o = SIDNEppClient('testdrs.domain-registry.nl',700,testuser,testpass)
#        s = self.o.domain_check('nfg.nl')
#        r = self.o.query(s, '//epp:result')[0]
#        self.failUnless(r.get("code") == "1000")

if __name__ == '__main__':
     unittest.main()
