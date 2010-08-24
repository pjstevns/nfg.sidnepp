

import urllib
import lxml.etree as et

BASEURL="http://names.nfgs.net/whois/%s"

class SIDNWhoisResult(object):


    def __init__(self, el):
        self._element = el

    def query(self, q):
        return self._element.xpath(q,namespaces=self.namespace)

class SIDNWhois(object):

    namespaces = {'w':'http://rxsd.domain-registry.nl/sidn-whois-drs50'}

    def __init__(self, domain):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s._result
        <Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}whois-response at ...>

        """
        self._result = et.fromstring(urllib.urlopen(BASEURL % domain).read())

    def xpath(self, q):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s.xpath('/whois-response')
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}whois-response at ...>]

        >>> code = s.xpath('/whois-response/domain/status/code')
        >>> code
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}code at ...>]

        >>> code[0].text
        'active'

        """
        return self._result.xpath(q.replace("/","/w:"),namespaces=self.namespaces)

    def getDomain(self):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s.getDomain()
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}domain at ...>]
        """
        return self.xpath('/whois-response/domain')

    def getRegistrar(self):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s.getRegistrar()
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}registrar at ...>]
        """
        return self.xpath('/whois-response/registrar')

    def getContact(self):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s.getContact()
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}contact at ...>, ...]
        """
        return self.xpath('/whois-response/contact')

    def getNameserver(self):
        """
        >>> s = SIDNWhois('nfg.nl')
        >>> s.getNameserver()
        [<Element {http://rxsd.domain-registry.nl/sidn-whois-drs50}nameserver at ...>]
        """
        return self.xpath('/whois-response/nameserver')


if __name__ == '__main__':
   import doctest
   doctest.testmod(optionflags=doctest.ELLIPSIS)

