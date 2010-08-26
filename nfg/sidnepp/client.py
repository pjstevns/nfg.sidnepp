#!/usr/bin/python

# interface for SIDN EPP 
#
# license: GPLv3
#
# copyright 2010, NFG Net Facilities Group BV, www.nfg.nl
#       
# Paul Stevens, paul@nfg.nl

from zope.interface import implements
import socket, struct, ssl
from lxml import etree


import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..','..'))

from nfg.sidnepp.interfaces import IEpp
from nfg.sidnepp.protocol import SIDNEppProtocol
from nfg.sidnepp.state import STATE_INIT, STATE_CONNECTED, STATE_SESSION, STATE_LOGGEDIN

class SIDNEppClient(SIDNEppProtocol):
    implements(IEpp)

    _connection_State = STATE_INIT
    
    # server frames
    _greeting = None
    _login = None

    def __init__(self, host=None, port=None, username=None, password=None,
                 ssl=True):
        super(SIDNEppClient, self).__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.connect()

    def connect(self):
        assert(self._connection_State == STATE_INIT) 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        if self.ssl:
            self._fd = ssl.wrap_socket(s)
        else:
            self._fd = s
        self._connection_State = STATE_CONNECTED

        self._greeting = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(self.hello())
        if self.username and self.password:
            self._login = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                    etree.tostring(self.login(self.username, self.password))

    def write(self, message):
        assert(self._connection_State > STATE_INIT)
        # validate

        if type(message) == etree._Element:
            message = self.render(message)
        else:
            self.parse(message)

        l = len(message)+4
        data = struct.pack(">L", l)
        try:
            self._fd.send(data)
            self._fd.send(message)
        except Exception:
            # re-connect
            self.close()
            self.connect()
            self._fd.send(data)
            self._fd.send(message)

        return self.read()

    def read(self):
        buf = self._fd.recv(4)
        need = struct.unpack(">L", buf)
        need = need[0]-4
        return self.parse(self._fd.recv(need))

    def close(self):
        self._fd.close()
        self._connection_State = STATE_INIT

    def getState(self):
        return self._connection_State

# commands

# 6.4 SESSION

    def hello(self):
        if self._connection_State == STATE_SESSION and self._greeting:
            return self.parse(self._greeting)

        assert(self._connection_State == STATE_CONNECTED)
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
          <hello/>
        </epp>"""
        result = self.write(xml)
        assert(self.query(result,"//epp:greeting"))
        self._connection_State = STATE_SESSION
        self._greeting = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(result)
        return result

    def login(self, login, password, newpassword=None, lang='NL'):
        if self._connection_State == STATE_LOGGEDIN and self._login:
            return self.parse(self._login)

        assert(self._connection_State == STATE_SESSION)
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
        result = self.write(xml)
        r = self.query(result, "//epp:result")
        if not r:
            result = self.read()
            r = self.query(result, "//epp:result")
        if r[0].attrib['code'] != '1000':
            raise Exception, "login failed. code was %s\nfull message:\n%s" % (
                r[0].attrib['code'], etree.tostring(r[0]))

        self._connection_State = STATE_LOGGEDIN
        self._login = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(result)
        return result

    def logout(self):
        assert(self._connection_State == STATE_LOGGEDIN) 
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xsi:schemaLocation="urn:ietf:params:xml:ns:epp-1.0 epp-1.0.xsd">
        <command>
        <logout/>
        </command>
        </epp>
        """
        r = self.write(xml)
        self.close()
        return r

    def poll(self, ack=None):
        assert(self._connection_State == STATE_LOGGEDIN) 
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?> 
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
        <command>
        <poll op="%s" %s/>
        </command>
        </epp>
        """
        op='req'
        msgid=''
        if ack:
            op='ack'
            msgid='msgID="%s"' % ack
        return self.write(xml % (op, msgid))

# 6.5 DOMAIN

    def domain_check(self, domain):
        e = self.e_epp
        d = self.e_domain
        return self.write(
            e.epp(e.command(e.check(d.check(d.name(domain)))))
        )

    def domain_info(self, domain):
        e = self.e_epp
        d = self.e_domain
        return self.write(
            e.epp(e.command(e.info(d.info(d.name(domain,hosts='all')))))
        )

    def domain_create(self, domain, data):
        pass

    def domain_update(self, domain, data):
        pass

    def domain_delete(self, domain):
        pass

    def domain_cancel_delete(self, domain):
        pass

    def domain_transfer(self, domain, data):
        pass

# 6.6 CONTACT

    def contact_check(self, contact):
        e = self.e_epp
        c = self.e_contact
        x = e.epp(e.command(e.check(c.check(c.id(contact)))))
        return self.write(x)

    def contact_info(self, contact):
        e = self.e_epp
        c = self.e_contact
        return self.write(e.epp(e.command(e.info(c.info(c.id(contact))))))

    def contact_create(self, contact, data):
        pass

    def contact_update(self, contact, data):
        pass

    def contact_delete(self, contact):
        e = self.e_epp
        c = self.e_contact
        return self.write(e.epp(e.command(e.delete(c.delete(c.id(contact))))))

# 6.7 NAMESERVERS

    def host_check(self, host):
        e = self.e_epp
        h = self.e_host
        return self.write(e.epp(e.command(e.check(h.check(h.name(host))))))

    def host_info(self, host):
        e = self.e_epp
        h = self.e_host
        return self.write(e.epp(e.command(e.info(h.info(h.name(host))))))

    def host_create(self, host, addr=None, ip="v4"):
        assert(ip in ['v4','v6'])
        e = self.e_epp
        h = self.e_host
        t = [h.name(host),]
        if addr:
            if type(addr) == type("1"):
                addr = [addr,]
            assert(type(addr) == type([1,]))
            [ t.append(h.addr(a,ip=ip)) for a in addr ]
        t = tuple(t)
        return self.write(e.epp(e.command(e.create(h.create(*t)))))

    def host_update(self, host, data):
        assert(type(data) == type({'a':'b'}))
        e = self.e_epp
        h = self.e_host
        t = [h.name(host),]
        for k,v in data.items():
            if k == 'add':
                [ t.append(h.add(h.addr(a))) for a in v ]
            elif k == 'rem':
                [ t.append(h.rem(h.addr(a))) for a in v ]
            
        t = tuple(t)
        return self.write(e.epp(e.command(e.update(h.update(*t)))))

    def host_delete(self, host):
        e = self.e_epp
        h = self.e_host
        return self.write(e.epp(e.command(e.delete(h.delete(h.name(host))))))

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
