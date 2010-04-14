
default: bin/buildout
	bin/buildout -v

bin/python:
	virtualenv --clear --no-site-packages --python=python2.6 --distribute .


bin/buildout: bin/python
	bin/easy_install zc.buildout


clean:
	rm -rf bin/ include/ lib/ eggs/ develop-eggs/ .installed.cfg 

