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

    _state = STATE_INIT
    
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
        assert(self._state == STATE_INIT) 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        if self.ssl:
            self._fd = ssl.wrap_socket(s)
        else:
            self._fd = s
        self._state = STATE_CONNECTED

        self._greeting = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(self.hello())
        if self.username and self.password:
            self._login = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                    etree.tostring(self.login(self.username, self.password))

    def write(self, message):
        assert(self._state > STATE_INIT)
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
            print "Oops, reconnecting"
            self.close()
            self.connect()
            self._fd.send(data)
            self._fd.send(message)

        return self.read()

    def read(self):
        buf = self.readall(self._fd, 4)
        need = struct.unpack(">L", buf)
        need = need[0]-4
        buf = self.readall(self._fd, need)
        return self.parse(buf)

    def close(self):
        self._fd.close()
        self._state = STATE_INIT

    def getState(self):
        return self._state

# commands

# 6.4 SESSION

    def hello(self):
        if self._state == STATE_SESSION and self._greeting:
            return self.parse(self._greeting)

        assert(self._state == STATE_CONNECTED)
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
          <hello/>
        </epp>"""
        result = self.write(xml)
        assert(self.query(result,"//epp:greeting"))
        self._state = STATE_SESSION
        self._greeting = '<?xml version="1.0" encoding="UTF-8"?>%s' % \
                etree.tostring(result)
        return result

    def login(self, login, password, newpassword=None, lang='NL'):
        if self._state == STATE_LOGGEDIN and self._login:
            return self.parse(self._login)

        assert(self._state == STATE_SESSION)
        e = self.e_epp
        x = e.epp(
            e.command(
                e.login(
                    e.clID(login),
                    e.pw(password),
                    e.options(e.version('1.0'), e.lang(lang)),
                    e.svcs(
                        e.objURI('urn:ietf:params:xml:ns:contact-1.0'),
                        e.objURI('urn:ietf:params:xml:ns:host-1.0'),
                        e.objURI('urn:ietf:params:xml:ns:domain-1.0'),
                        e.svcExtension(
                            e.extURI('urn:ietf:params:xml:ns:sidn-ext-epp-1.0')
                        )
                    )
                )
            )
        )
        s = self.write(x)
        r = self.query(s, "//epp:result")
        if not r:
            s = self.read()
            r = self.query(s, "//epp:result")
        if int(r[0].get('code')) != 1000:
            raise Exception, "login failed. code was %s\nfull message:\n%s" % (
                r[0].get('code'), self.render(r[0]))

        self._state = STATE_LOGGEDIN
        self._login = self.render(s)
        return s

    def logout(self):
        assert(self._state == STATE_LOGGEDIN) 
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
        assert(self._state == STATE_LOGGEDIN) 
        e = self.e_epp
        if ack:
            poll = e.poll(op='ack',msgID=ack)
        else:
            poll = e.poll(op='req')
        return self.write(e.epp(e.command(poll)))

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
        e = self.e_epp
        d = self.e_domain
        nslist = []
        for ns in data['ns']:
            nslist.append(d.hostObj(ns))
        nslist = tuple(nslist)
        x = e.epp(
            e.command(
                e.create(
                    d.create(
                        d.name(domain),
                        d.ns(*nslist),
                        d.registrant(data['owner']),
                        d.contact(data['admin'], type='admin'),
                        d.contact(data['tech'], type='tech'),
                        d.authInfo(
                            d.pw('unused')
                        )
                    )
                )
            )
        )
        return self.write(x)

    def _build_domain_update(self, key, value):
        d = self.e_domain
        u = []
        if key in ['add','rem']:
            if value.has_key('ns'):
                l = [ d.hostObj(t) for t in value['ns'] ]
                l = tuple(l)
                u.append(d.ns(*l))
            if value.has_key('tech'):
                if type(value['tech']) != type([1,]):
                    value['tech'] = [value['tech'],]
                [ u.append(d.contact(t, type='tech')) for t in value['tech'] ]
            if value.has_key('admin'):
                u.append(d.contact(value['admin'], type='admin'))
        if key in ['chg']:
            u.append(d.registrant(value['owner']))
        return tuple(u)

    def domain_update(self, domain, data):
        keys = data.keys()
        for k in keys:
            assert(k in ['add','chg','rem'])
        e = self.e_epp
        d = self.e_domain
        add = ()
        chg = ()
        rem = ()
        for k,v in data.items():
            if k == 'add':
                add = self._build_domain_update(k, v)
            elif k == 'rem':
                rem = self._build_domain_update(k, v)
            elif k == 'chg':
                chg = self._build_domain_update(k, v)

        x = e.epp(
            e.command(
                e.update(
                    d.update(
                        d.name(domain),
                        d.add(*add),
                        d.rem(*rem),
                        d.chg(*chg),
                    )
                )
            )
        )
        return self.write(x)

    def domain_delete(self, domain):
        e = self.e_epp
        d = self.e_domain
        x = e.epp(
            e.command(
                e.delete(
                    d.delete(
                        d.name(domain)
                    )
                )
            )
        )
        return self.write(x)

    def domain_cancel_delete(self, domain):
        e = self.e_xsi
        s = self.e_sidn
        x = e.epp(
            e.extension(
                s.command(
                    s.domainCancelDelete(
                        s.name(domain)
                    )
                )
            )
        )
        return self.write(x)

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

    def _build_contact_info(self, data):
        c = self.e_contact
        addrInfo = []
        postalInfo = []
        contactInfo = []

        if data.has_key('name'):
            postalInfo = [c.name(data['name']),]
        if data.has_key('org'):
            postalInfo.append(c.org(data['org']))

        if data.has_key('street'):
            addrInfo = [ c.street(x) for x in data['street'] ]
        addrInfo.append(c.city(data['city']))
        if data.has_key('sp'):
            addrInfo.append(c.sp(data['sp']))
        if (data.has_key('cc') and data['cc'] == 'NL') or data.has_key('pc'):
            addrInfo.append(c.pc(data['pc']))
        addrInfo.append(c.cc(data['cc']))

        if len(addrInfo):
            addrInfo = tuple(addrInfo)
            postalInfo.append(c.addr(*addrInfo))

        contactInfo.append(c.postalInfo(type='loc', *postalInfo))

        if data.has_key('voice'):
            contactInfo.append(c.voice(data['voice']))
        if data.has_key('fax'):
            contactInfo.append(c.fax(data['fax']))
        if data.has_key('email'):
            contactInfo.append(c.email(data['email']))
        contactInfo.append(c.authInfo(c.pw('unused')))
        return tuple(contactInfo)

    def _build_legal_info(self, data):
        s = self.e_sidn

        sidnInfo = []
        if data.has_key('legalForm'):
            sidnInfo = [s.legalForm(data['legalForm']),]
        if data.has_key('legalFormRegNo'):
            sidnInfo.append(s.legalFormRegNo(data['legalFormRegNo']))
        return tuple(sidnInfo)

    def contact_create(self, contact, data):
        e = self.e_epp
        s = self.e_sidn
        c = self.e_contact

        contactInfo = self._build_contact_info(data)
        sidnInfo = self._build_legal_info(data)

        x = e.epp(
            e.command(
                e.create(c.create(c.id(contact), *contactInfo)),
                e.extension(s.ext(s.create(s.contact(*sidnInfo))))
            )
        )
        return self.write(x)
        

    def contact_update(self, contact, data):
        e = self.e_epp
        s = self.e_sidn
        c = self.e_contact
        extension = ()
        change = ()

        contactInfo = self._build_contact_info(data)
        if contactInfo:
            change = c.chg(*contactInfo)

        sidnInfo = self._build_legal_info(data)
        if sidnInfo:
            extension = e.extension(s.ext(s.update(s.contact(*sidnInfo))))

        x = e.epp(e.command(
            e.update(c.update(c.id(contact), change)), 
            *extension)
        )
        return self.write(x)

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
