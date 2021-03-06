#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# fake-shaarli-server.py - Fake out Shaarli REST API
# Copyright (C) 2022  Chris Clark
"""Just enough API support to allow Shaarlier and python-shaarli-client to run

Uses WSGI, see http://docs.python.org/library/wsgiref.html

Python 2 or Python 3
"""

import cgi
import os
try:
    import json
except ImportError:
    json = None
import logging
import mimetypes
from pprint import pprint

import socket
import struct
import sys
from wsgiref.simple_server import make_server


version_tuple = (0, 0, 1)
version = __version__ = '%d.%d.%d' % version_tuple
__author__ = 'clach04'

def force_bool(in_bool):
    """Force string value into a Python boolean value
    Everything is True with the exception of; false, off, and 0"""
    value = str(in_bool).lower()
    if value in ('false', 'off', '0'):
        return False
    else:
        return True

ALWAYS_RETURN_404 = force_bool(os.environ.get('ALWAYS_RETURN_404', True))
DEFAULT_SERVER_PORT = 8000


log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(level=logging.DEBUG)


def to_bytes(in_str):
    # could choose to only encode for Python 3+
    return in_str.encode('utf-8')

def not_found(environ, start_response):
    """serves 404s."""
    #start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    #return ['Not Found']
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [to_bytes('''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL /??????? was not found on this server.</p>
</body></html>''')]


def determine_local_ipaddr():
    local_address = None

    # Most portable (for modern versions of Python)
    if hasattr(socket, 'gethostbyname_ex'):
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip.startswith('127.'):
                local_address = ip
                break
    # may be none still (nokia) http://www.skweezer.com/s.aspx/-/pypi~python~org/pypi/netifaces/0~4 http://www.skweezer.com/s.aspx?q=http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib has alonger one

    if sys.platform.startswith('linux'):
        import fcntl

        def get_ip_address(ifname):
            ifname = ifname.encode('latin1')
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
            )[20:24])

        if not local_address:
            for devname in os.listdir('/sys/class/net/'):
                try:
                    ip = get_ip_address(devname)
                    if not ip.startswith('127.'):
                        local_address = ip
                        break
                except IOError:
                    pass

    # Jython / Java approach
    if not local_address and InetAddress:
        addr = InetAddress.getLocalHost()
        hostname = addr.getHostName()
        for ip_addr in InetAddress.getAllByName(hostname):
            if not ip_addr.isLoopbackAddress():
                local_address = ip_addr.getHostAddress()
                break

    if not local_address:
        # really? Oh well lets connect to a remote socket (Google DNS server)
        # and see what IP we use them
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 53))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith('127.'):
            local_address = ip

    return local_address



# dumb global dispatcher
# TODO exception handling
class DefaultDispatcher:
    def search_links(self, *args, **kwargs):
        """Search for URL(s)
        http://shaarli.github.io/api-documentation/#links-links-collection-get
        Be prepared for; offset, limit, searchterm, searchtags, visibility
        returns a list, empty or sample single entry result:

            [
                        {
                            "id": 345,
                            "url": "http://foo.bar",
                            "shorturl": "1H3Srg",
                            "title": "Link title",
                            "description": "Hello, world!",
                            "tags": [
                              "foo",
                              "bar"
                            ],
                            "private": False,
                            "created": "2000-01-01T00:00:00+00:00",
                            "updated": "2000-01-01T00:00:00+00:00"
                        }

            ]
        """
        print('search_links(): ' + repr(kwargs))
        return []

    def search_tags(self, *args, **kwargs):
        """Search for tags
        http://shaarli.github.io/api-documentation/#links-tags-collection-get
        Be prepared for; offset, limit, visibility
        returns a list, empty or sample single entry result:

            [
              {
                "name": "Tutorial",
                "occurences": 47
              }
            ]
        """
        print('search_tags(): ' + repr(kwargs))
        return []

    def add_link(self, *args, **kwargs):
        """Add a single URL bookmark
        http://shaarli.github.io/api-documentation/#links-links-collection-post
        Be prepared for;
            "url": "https://www.google.com/",
            "title": "Some Title",
            "description": "Some Description",
            "tags": ["foo", "bar"],
            "private": False

        Return a dictionary, sample:

            {
                "id": 1,  # No good default
                "shorturl": "111111",  # No good default
                "url": "",
                "title": "",
                "description": "",
                "tags": ["foo", "bar"],
                "private": False,
                "created": "2000-01-01T00:00:00+00:00",
                "updated": "2000-01-01T00:00:00+00:00"
            }
        Caller can deal with missing returned entries and will default if omitted
        """
        print('add_link(): ' + repr(kwargs))
        return kwargs  # assume it's valid

dispatcher = DefaultDispatcher()


def shaarli_rest_api_wsgi(environ, start_response):
    """Simple WSGI application that implements bare minimum of
    http://shaarli.github.io/api-documentation/ so that
    https://github.com/dimtion/Shaarlier and
    https://github.com/shaarli/python-shaarli-client completes
    """
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    result= []

    path_info = environ['PATH_INFO']
    request_method = environ['REQUEST_METHOD']
    # from https://wsgi.readthedocs.io/en/latest/definitions.html
    print('debug ' + environ['SERVER_PROTOCOL'])
    print('debug ' + environ['HTTP_HOST'])
    print('debug ' + environ['SERVER_NAME'])
    print('debug ' + environ['SERVER_PORT'])
    print('debug ' + environ['SCRIPT_NAME'])

    if 'GET' == request_method:
        # Returns a dictionary in which the values are lists
        get_dict = cgi.parse_qs(environ['QUERY_STRING'])  # FIXME not needed here, defer to later when GET is needed (useless OP when POST/PUT used)

        if path_info and path_info.startswith('/api/v1/info'):
            # http://shaarli.github.io/api-documentation/#links-instance-information-get
            # python -m shaarli_client.main  get-info
            server = environ['HTTP_HOST'] or (environ['SERVER_NAME'] + ':' + environ['SERVER_PORT'])
            #print(server)
            default_info_dict = {
              "global_counter": 0,
              "private_counter": 0,
              "settings": {
                "title": "Fake Shaarli v%s REST API v1" % (__version__,),
                "header_link": environ['wsgi.url_scheme'] + '://' + server + '/' + environ['SCRIPT_NAME'],  # see https://peps.python.org/pep-0333/#url-reconstruction
                "timezone": "Europe/Paris",
                "enabled_plugins": [
                ],
                "default_private_links": True
              }
            }
            fake_info_str = json.dumps(default_info_dict)
            # string sample
            """{
  "global_counter": 654,
  "private_counter": 123,
  "settings": {
    "title": "My links",
    "header_link": "https://foo.bar/shaarli",
    "timezone": "Europe/Paris",
    "enabled_plugins": [
      "qrcode",
      "markdown"
    ],
    "default_private_links": true
  }
}
"""
        elif path_info and path_info.startswith('/api/v1/links'):
            # http://shaarli.github.io/api-documentation/#links-links-collection-get
            # /links{?offset,limit,searchterm,searchtags,visibility}
            # get_dict == {'searchterm': ['https://www.immae.eu/'], 'limit': ['1'], 'offset': ['0']}
            #
            # python -m shaarli_client.main  get-links
            # python -m shaarli_client.main  get-links --searchterm hello
            # Shaarlier will then take that result and update the on screen info, e.g. description, tags and title
            # when return empty list, looks like it gets details from site? or was passed in via android share intent?

            # Sample single entry string
            """[
                  {
                    "id": 345,
                    "url": "http://foo.bar",
                    "shorturl": "1H3Srg",
                    "title": "Link title",
                    "description": "Hello, world!",
                    "tags": [
                      "foo",
                      "bar"
                    ],
                    "private": false,
                    "created": "2015-05-05T12:30:00+03:00",
                    "updated": "2015-05-06T14:30:00+03:00"
                  }
                ]
            """
            '''
            # Empty list
            fake_info_str = "[]"
            '''
            bookmark_list = dispatcher.search_links(**get_dict)
            fake_info_str = json.dumps(bookmark_list)
        elif path_info and path_info.startswith('/api/v1/tags'):
            # http://shaarli.github.io/api-documentation/#links-tags-collection-get
            # /tags{?offset,limit,visibility}

            # sample string
            """[
                  {
                    "name": "Tutorial",
                    "occurences": 47
                  }
                ]
            """
            tag_list = dispatcher.search_tags(**get_dict)
            fake_info_str = json.dumps(tag_list)
        else:
            # unsupported GET
            print('Unsupported GET path_info %r' % (path_info,))
            print('%r with payload %r' % (request_method, get_dict))
            print(repr(environ['QUERY_STRING']))
            # TODO dump more info?

            #raise NotImplemented()
            if ALWAYS_RETURN_404:
                # Disable this to send 200 and empty body
                return not_found(environ, start_response)
            fake_info_str = ''
    else:
        # Assume PUT or POST

        # the environment variable CONTENT_LENGTH may be empty or missing
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        # Read POST body
        request_body = environ['wsgi.input'].read(request_body_size)
        link_payload_dict = json.loads(request_body)
        print('%r with payload %r' % (request_method, link_payload_dict))

        if path_info and path_info.startswith('/api/v1/links/'):
            #  '/api/v1/links/345'
            # python -m shaarli_client.main  put-link --title title --url http://something.com 345
            # update exsting entry, path is the "id"
            # assume PUT
            fake_info_str = """{
  "id": 345,
  "url": "http://foo.bar",
  "shorturl": "1H3Srg",
  "title": "Link title",
  "description": "Hello, world!",
  "tags": [
    "foo",
    "bar"
  ],
  "private": false,
  "created": "2015-05-05T12:30:00+03:00",
  "updated": "2015-05-06T14:30:00+03:00"
}
"""
        elif path_info and path_info.startswith('/api/v1/links'):
            # http://shaarli.github.io/api-documentation/#links-links-collection-get
            # http://shaarli.github.io/api-documentation/#links-links-collection-post
            # TODO both /sw.js (used by python-shaarli-client) and '/jw' (by shaarlier android share) both request 'text/plain'
            # TODO '/api/v1/tags' used by shaarlier android share
            # TODO "GET /api/v1/links?offset=0&limit=1&searchterm=https%3A%2F%2Fwww.immae.eu%2F HTTP/1.1" used by shaarlier android share - looking for dupes
            # 404 does not elict an error response from shaarlier android share
            # TODO both post-link put-link ?

            # assume POST
            # http://shaarli.github.io/api-documentation/#links-links-collection-post
            # python -m shaarli_client.main  post-link --title title --url http://something.com
            # python -m shaarli_client.main  post-link --title title --url http://something.com --description "cool stuff"
            # get_dict == EMPTY - as expecting json payload
            # request_body = '{"url":"https:\\/\\/www.immae.eu\\/","title":"Immae","description":"","tags":[""],"private":false}'

            # handle NULL (missing) tags (seen with python-shaarli-client) and an empty string tags (seen with Shaarlier)
            if link_payload_dict['tags']:
                processed_tags = [x for x in link_payload_dict['tags'] if x]
            else:
                processed_tags = []
            link_payload_dict['tags'] = processed_tags

            default_bookmark_dict = {
              "id": 1,  # No good default
              "shorturl": "111111",  # No good default
              "url": "",
              "title": "",
              "description": "",
              "tags": [],
              "private": False,
              "created": "2000-01-01T00:00:00+00:00",
              "updated": "2000-01-01T00:00:00+00:00"
            }
            result_bookmark = dispatcher.add_link(**link_payload_dict)
            default_bookmark_dict.update(result_bookmark)
            fake_info_str = json.dumps(default_bookmark_dict)

            # Sample text result
            """{
      "id": 345,
      "url": "http://foo.bar",
      "shorturl": "1H3Srg",
      "title": "Link title",
      "description": "Hello, world!",
      "tags": [
        "foo",
        "bar"
      ],
      "private": false,
      "created": "2015-05-05T12:30:00+03:00",
      "updated": "2015-05-06T14:30:00+03:00"
    }
    """
            status = '201 OK'
        else:
            # Not supported, dump out information about the request
            #print(environ)
            #pprint(environ)
            print('PATH_INFO %r' % environ['PATH_INFO'])
            print('CONTENT_TYPE %r' % environ['CONTENT_TYPE'])
            print('QUERY_STRING %r' % environ['QUERY_STRING'])
            print('QUERY_STRING dict %r' % get_dict)
            print('REQUEST_METHOD %r' % environ['REQUEST_METHOD'])
            #print('environ %r' % environ) # DEBUG, potentially pretty print, but dumping this is non-default
            #print('environ:') # DEBUG, potentially pretty print, but dumping this is non-default
            #pprint(environ, indent=4)
            print('Filtered headers, HTTP*')
            for key in environ:
                if key.startswith('HTTP_'):  # TODO potentially startswith 'wsgi' as well
                    # TODO remove leading 'HTTP_'?
                    print('http header ' + key + ' = ' + repr(environ[key]))

            print('POST body %r' % request_body)
            if environ['CONTENT_TYPE'] == 'application/json' and json and request_body:
                # 1. Validate the payload - with stacktrace on failure
                # 2. Pretty Print/display the payload
                print('POST json body\n-------------\n%s\n-------------\n' % json.dumps(json.loads(request_body), indent=4))
            #print('environ %r' % environ)
            if ALWAYS_RETURN_404:
                # Disable this to send 200 and empty body
                return not_found(environ, start_response)
            fake_info_str = ''
    result.append(to_bytes(fake_info_str))

    start_response(status, headers)
    return result


def main(argv=None):
    print('Python %s on %s' % (sys.version, sys.platform))
    server_port = int(os.environ.get('PORT', DEFAULT_SERVER_PORT))

    httpd = make_server('', server_port, shaarli_rest_api_wsgi)
    print("Serving on port %d..." % server_port)
    print("ALWAYS_RETURN_404 = %r" % ALWAYS_RETURN_404)
    local_ip = determine_local_ipaddr()
    log.info('Starting server: %r', (local_ip, server_port))
    httpd.serve_forever()

if __name__ == "__main__":
    sys.exit(main())
