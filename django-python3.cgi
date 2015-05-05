#!/home/user/.pyenv/versions/envname/bin/python
# encoding: utf-8
"""
django-.cgi

A simple cgi script which uses the django WSGI to serve requests.

Code copy/pasted from PEP-0333 and then tweaked to serve django.
http://www.python.org/dev/peps/pep-0333/#the-server-gateway-side

This script assumes django is on your sys.path, and that your site code is at
/djangoproject/src. Copy this script into your cgi-bin directory (or do
whatever you need to to make a cgi script executable on your system), and then
update the paths at the bottom of this file to suit your site.

This is probably the slowest way to serve django pages, as the python
interpreter, the django code-base and your site code has to be loaded every
time a request is served. FCGI and mod_python solve this problem, use them if
you can.

In order to speed things up it may be worth experimenting with running
uncompressed zips on the sys.path for django and the site code, as this can be
(theorectically) faster. See PEP-0273 (specifically Benchmarks).
http://www.python.org/dev/peps/pep-0273/

Make sure all python files are compiled in your code base. See
http://docs.python.org/lib/module-compileall.html

"""


import os, sys

# Change this to the directory above your site code.
# sys.path.append("/home/user/local/lib/python3.4/site-packages")
# sys.path.append("/djangoproject/src")

def run_with_cgi(application):

    environ                      = dict(os.environ.items())
    environ['wsgi.input']        = sys.stdin.buffer
    environ['wsgi.errors']       = sys.stderr.buffer
    environ['wsgi.version']      = (1,0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']     = True

    if environ.get('HTTPS','off') in ('on','1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set  = []
    headers_sent = []

    def write(data):
        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
             # Before the first output, send the stored headers
             status, response_headers = headers_sent[:] = headers_set
             sys.stdout.buffer.write(('Status: %s\r\n' % status).encode("ascii"))
             for header in response_headers:
                 sys.stdout.buffer.write(('%s: %s\r\n' % header).encode("ascii"))
             sys.stdout.buffer.write(('\r\n').encode("ascii"))

        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

    def start_response(status,response_headers,exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
            finally:
                exc_info = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status,response_headers]
        return write

    result = application(environ, start_response)
    try:
        for data in result:
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write('')   # send headers now if body was empty
    finally:
        if hasattr(result,'close'):
            result.close()

# Change to the name of your settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'application.settings'
from django.core.wsgi import get_wsgi_application
run_with_cgi(get_wsgi_application())
