#!/usr/bin/python


import unittest

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..','..'))

from nfg.sidnepp.protocol import SIDNEppProtocol
from nfg.sidnepp.client import SIDNEppClient

testserver = 'localhost'
testport   = 7000
testuser   = 'fakeuser'
testpass   = 'fakepass'

class testSIDNEppProtocol(unittest.TestCase):

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

    def test_parse(self):
        self.o.parse(self.xml)

    def testQuery(self):
        e = self.o.parse(self.xml)
        r1 = e.xpath('//epp:command', namespaces={'epp':"urn:ietf:params:xml:ns:epp-1.0"})
        self.failUnless(len(r1) == 1)
        r2 = self.o.query(e, "//epp:command")
        self.failUnless(r1 == r2)
        r3 = self.o.query(e,"//epp:login")
        self.failUnless(type(r3) == type(r2))

    def testMaker(self):
        e = self.o.e_epp
        x = e.epp(
            e.command(
                e.login()
            )
        )

        expect="""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <login/>
  </command>
</epp>
"""
        self.failUnless(expect==self.o.render(x))

        h = self.o.e_host
        x = e.epp(
            e.command(
                e.create(
                    h.create(
                        h.name("ns10.nfgs.net"),
                        h.addr("194.109.214.3", ip="v4"),
                    )
                )
            )
        )
        expect="""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <create>
      <host:create xmlns:host="urn:ietf:params:xml:ns:host-1.0">
        <host:name>ns10.nfgs.net</host:name>
        <host:addr ip="v4">194.109.214.3</host:addr>
      </host:create>
    </create>
  </command>
</epp>
"""
        self.failUnless(expect==self.o.render(x))


class testSIDNEppClient(unittest.TestCase):

    def setUp(self):
        self.o = SIDNEppClient(host=testserver,
                               port=testport,
                               username=testuser,
                               password=testpass, 
                               ssl=False)

    def tearDown(self):
        try:
            self.o.logout()
        except AssertionError:
            pass
# 6.4 sessions

    def testLogin(self):
        s = self.o.login(testuser, testpass)
        r = self.o.query(s, '//epp:result')
        self.failUnless(len(r) > 0)

    def testLogout(self):
        s = self.o.logout()
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1500)

    def testPoll(self):
        s = self.o.poll()
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1300)
        s = self.o.poll('fake')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 2308)

# 6.5 domains

    def testDomainCheck(self):
        s = self.o.domain_check('nfg.nl')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000, r.get("code"))
        r = self.o.query(s, '//domain:name')[0]
        self.failUnless(r.get("avail") == "false")

    def testDomainInfo(self):
        s = self.o.domain_info('nfg.nl')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testDomainCreate(self):
        pass

    def testDomainUpdate(self):
        pass

    def testDomainDelete(self):
        pass

    def testDomainCancelDelete(self):
        pass

    def testDomainTransfer(self):
        pass

# 6.6 contacts

    def testContactCheck(self):
        pass

    def testContactInfo(self):
        pass

    def testContactCreate(self):
        pass

    def testContactUpdate(self):
        pass

    def testContactDelete(self):
        pass

# 6.7 hosts
    def testHostCheck(self):
        s = self.o.host_check('ns.nfg.nl')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        r = self.o.query(s, '//host:name')[0]
        self.failUnless(r.get("avail") == "false")

    def testHostInfo(self):
        s = self.o.host_info('ns.nfg.nl')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        r = self.o.query(s, "//host:addr[@ip='v4']")[0]
        self.failUnless(r.text == "194.109.214.3")

    def testHostCreate(self):
        s = self.o.host_create('ns10.nfgs.net','194.109.214.10',ip="v4")
        self.o.render(s)

    def testHostUpdate(self):
        pass

    def testHostDelete(self):
        pass

if __name__ == '__main__':
     unittest.main()

