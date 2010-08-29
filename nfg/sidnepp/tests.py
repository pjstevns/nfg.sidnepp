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

    xml1 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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

    xml2="""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<epp xmlns:sidn-ext-epp="http://rxsd.domain-registry.nl/sidn-ext-epp-1.0" xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <create>
      <contact:create xmlns:contact="urn:ietf:params:xml:ns:contact-1.0">
        <contact:id>JAN100827-NFGNT</contact:id>
        <contact:postalInfo type="loc">
          <contact:name>Jan Janssen BV</contact:name>
          <contact:org>Technisch Beheer</contact:org>
          <contact:addr>
            <contact:street>Wolvenplein 16</contact:street>
            <contact:city>Utrecht</contact:city>
            <contact:pc>3512CK</contact:pc>
            <contact:cc>NL</contact:cc>
          </contact:addr>
        </contact:postalInfo>
        <contact:voice>+31.0858779997</contact:voice>
        <contact:fax>+31.0858779996</contact:fax>
        <contact:email>test@nfg.nl</contact:email>
        <contact:authInfo>
          <contact:pw>unused</contact:pw>
        </contact:authInfo>
      </contact:create>
    </create>
    <extension>
      <sidn-ext-epp:ext>
        <sidn-ext-epp:create>
          <sidn-ext-epp:contact>
            <sidn-ext-epp:legalForm>BV</sidn-ext-epp:legalForm>
            <sidn-ext-epp:legalFormRegNo>14633770</sidn-ext-epp:legalFormRegNo>
          </sidn-ext-epp:contact>
        </sidn-ext-epp:create>
      </sidn-ext-epp:ext>
    </extension>
  </command>
</epp>

"""

    def setUp(self):
        self.o = SIDNEppProtocol()

    def test_parse(self):
        self.o.parse(self.xml1)
        self.o.parse(self.xml2)

    def testQuery(self):
        e = self.o.parse(self.xml1)
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
<epp xmlns:sidn-ext-epp="http://rxsd.domain-registry.nl/sidn-ext-epp-1.0" xmlns="urn:ietf:params:xml:ns:epp-1.0">
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
<epp xmlns:sidn-ext-epp="http://rxsd.domain-registry.nl/sidn-ext-epp-1.0" xmlns="urn:ietf:params:xml:ns:epp-1.0">
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
    userdata = dict(
        name='Jan Janssen BV',
        org='Technisch Beheer',
        street=['Wolvenplein 16'],
        city='Utrecht',
        pc='3512CK',
        cc='NL',
        voice='+31.0858779997',
        fax='+31.0858779996',
        email='test@nfg.nl',
        legalForm='BV',
        legalFormRegNo='14633770',
    )

    hostq = []
    contactq = []

    def setUp(self):
        self.o = SIDNEppClient(host=testserver,
                               port=testport,
                               username=testuser,
                               password=testpass, 
                               ssl=False)

    def tearDown(self):
        try:
            for h in self.hostq:
                self.o.host_delete(h)
            self.hostq = []
            for u in self.contactq:
                self.o.contact_delete(u)
            self.contactq = []

            self.o.logout()
        except:
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
        s = self.o.contact_check('STE002126-NFGNT')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testContactInfo(self):
        s = self.o.contact_info('STE002126-NFGNT')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testContactCreate(self):
        s = self.o.contact_create('JANJANSSENBV', self.userdata)
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        r = self.o.query(s, '//contact:id')[0]
        s = self.o.contact_delete(r.text)
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testContactUpdate(self):
        s = self.o.contact_create('JANJANSSENBV', self.userdata)
        userid = self.o.query(s, '//contact:id')[0].text
        self.contactq.append(userid)

        data = dict(
            name = 'Jan Janssen en co. BV',
            org = 'Operationeel beheer',
            street = ['Wolvenplein 16-bis'],
            pc = '3512CK',
            city = 'Utrecht',
            cc = 'NL'
        )
        s = self.o.contact_update(userid, data)
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

        s = self.o.contact_info(userid)
        r = self.o.query(s,'//contact:name')[0].text
        self.failUnless(r == data['name'])

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
        s = self.o.host_create('ns10.nfgs.net')
        self.hostq.append('ns10.nfgs.net')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

        s = self.o.host_create('ns10.nfg.nl','194.109.214.3')
        self.hostq.append('ns10.nfg.nl')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testHostUpdate(self):
        s = self.o.host_create('ns99.nfg.nl','194.109.214.123')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        self.hostq.append('ns99.nfg.nl')
        s = self.o.host_update('ns99.nfg.nl',
                               {
                                   'add': ['194.109.214.124'], 
                                   'rem': ['194.109.214.123']
                               }
                              )
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)

    def testHostDelete(self):
        s = self.o.host_create('ns99.nfgs.net')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        s = self.o.host_delete('ns99.nfgs.net')
        r = self.o.query(s, '//epp:result')[0]
        self.failUnless(int(r.get("code")) == 1000)
        

if __name__ == '__main__':
     unittest.main()

