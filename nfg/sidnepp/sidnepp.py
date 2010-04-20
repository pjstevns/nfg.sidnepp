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


from twisted.internet import reactor, protocol
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

class EPPClient(Protocol):

    def dataReceived(self, data):
        print 'received', data

    def connectionLost(self, reason):
        print 'connection lost. reason:', reason


class EPPClientFactory(ReconnectingClientFactory):
    
    def startedConnecting(self, connector):
        print "start connection", connector

    def buildProtocol(self, addr):
        print "build protocol"
        self.resetDelay()
        EPPClient()

    def clientConnectionLost(self, connector, reason):
        print "connection lost. reason:", reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print "connection failed. reason:", reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)

class SIDNEpp:
    implements(IEpp)

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        f = EPPClientFactory()
        reactor.connectTCP(host, port, f)
        reactor.run()

    def hello(self):
        pass

    def login(self, login, password, newpassword=None, lang='NL'):
        pass

    def logout(self):
        pass

    def poll(self, ack=None):
        pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    SIDNEpp('testdrs.domain-registry.nl',700)

