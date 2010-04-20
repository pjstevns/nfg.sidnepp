#!/usr/bin/python


from sidnepp import SIDNEpp


if __name__ == '__main__':
    o = SIDNEpp('testdrs.domain-registry.nl',700)
    o.hello()
