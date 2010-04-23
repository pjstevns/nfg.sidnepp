#!/usr/bin/python


from sidnepp import SIDNEpp
from lxml import etree

import unittest

testuser='300271'
testpass='c2155d6292'

class testSidnEPP(unittest.TestCase):

    def setUp(self):
        self.o = SIDNEpp('testdrs.domain-registry.nl',700)

    def testHello(self):
        s = self.o.hello()
        print s.xpath('/a:epp/greeting/svid')

#        self.failUnless(len(s) > 0)
#
#    def testLogin(self):
#        s = self.o.login(testuser, testpass)
#        self.failUnless(len(s) > 0)
#
#    def testLogout(self):
#        self.o.login(testuser, testpass)
#        s = self.o.logout()
#        self.failUnless('result code="1000"' in s)


if __name__ == '__main__':
     unittest.main()
