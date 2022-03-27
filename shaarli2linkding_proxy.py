#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# shaarli2linkding_proxy.py - Fake out Shaarli REST API and redirect (some) to LinkDing
# Copyright (C) 2022  Chris Clark
"""Just enough API support to allow Shaarlier to post to a LinkDing server

Python 2 or Python 3

  * https://github.com/sissbruecker/linkding/
  * https://github.com/dimtion/Shaarlier
  * https://github.com/shaarli/Shaarli
  
"""

import os
import sys

import requests  # https://github.com/psf/requests

import fake_shaarli_server  # https://github.com/clach04/fake-shaarli-server


linkding_token = os.environ['LINKDING_TOKEN']
linkding_uri = os.environ['LINKDING_URI']


class LinkDingDispatcher(fake_shaarli_server.DefaultDispatcher):
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
        print('LinkDingDispatcher.add_link(): ' + repr(kwargs))


        method = 'POST'
        endpoint = 'api/bookmarks/'  # will get 404 from LinkDing if have //api/bookmarks/ versus /api/bookmarks/
        verify_certs = True

        # TODO remove trailing '/' from uri, see 404 note below
        global linkding_uri  # fixme, make this a param into __init__ and store in self
        while linkding_uri[-1] == '/':
            linkding_uri = linkding_uri[:-1]

        # https://github.com/sissbruecker/linkding/blob/master/docs/API.md#authentication
        headers = {'Authorization': 'Token %s' % linkding_token}
        endpoint_uri = '%s/%s' % (linkding_uri, endpoint)

        # https://github.com/sissbruecker/linkding/blob/master/docs/API.md#bookmarks
        bookmark_dict = {
          "url": kwargs["url"],
          "title": kwargs["title"],
          "description": kwargs["description"],
          "tag_names": kwargs["tags"]  # rename
          # private is ignored/dropped
        }

        result = requests.request(
                    method,
                    endpoint_uri,
                    headers=headers,
                    json=bookmark_dict,
                    verify=verify_certs
                )

        print(result)
        # expect 201 on success, NOTE duplicates will not be created, if there is an existing entry it will be overwritten (potentially loosing data)
        print(result.status_code)
        # TODO ifnot 201 raise an error so fake server can also raise a reasonable error and report to Shaarli client
        result_bookmark = result.json() # {"id":6,"url":"https://example.com","title":"Example title","description":"Example description","website_title":"Example Domain","website_description":null,"tag_names":["tag1","tag2"],"date_added":"2022-03-27T22:44:34.185359Z","date_modified":"2022-03-27T22:44:34.185398Z"}

        kwargs["id"] = result_bookmark["id"]
        kwargs["private"] =  False  # no mapping, so default
        # TODO reformat ISO string
        """
        "created": "2000-01-01T00:00:00+00:00"  --  "date_added":"2022-03-27T22:44:34.185359Z",
        "updated": "2000-01-01T00:00:00+00:00"  --  "date_modified":"2022-03-27T22:44:34.185398Z"
        """
        return kwargs  # FIXME look up 

fake_shaarli_server.dispatcher = LinkDingDispatcher()


def main(argv=None):
    fake_shaarli_server.main(argv)


if __name__ == "__main__":
    sys.exit(main())
