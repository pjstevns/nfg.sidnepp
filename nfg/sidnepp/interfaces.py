

from zope.interface import Interface, Attribute

class IEpp(Interface):

    host = Attribute(""" remote EPP server we want to connect to""")
    port = Attribute(""" remote EPP port we want to connect to""")

    def login(login, password, newpassword=None, lang='NL'):
        """ initialize session, and optionaly set new password """

    def logout():
        """ end session """

    def poll(ack=None):
        """ pop message from the queue, or acknowledge message """



