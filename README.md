# fake-shaarli-server

Python implementation of _some_ of the [Shaarli REST API](http://shaarli.github.io/api-documentation/)

Just enough to convince the [Shaarlier Android app](https://github.com/dimtion/Shaarlier/) it's a real server.
Also (partially) works with [python-shaarli-client](https://github.com/shaarli/python-shaarli-client).

This doesn't actual do anything and is essentially non-functional. It completely ignores security (JWT) tokens (it does not handle the deprecated username/password authentication option). Basicallty, don't use it ;) Use https://github.com/shaarli/Shaarli instead :)


## Running

### shaarli2linkding_proxy.py

Map from [Shaarli REST API v1](http://shaarli.github.io/api-documentation) into
[LinkDing REST API](https://github.com/sissbruecker/linkding/blob/master/docs/API.md)

Right now this only supports tag lookup and creating new entries (or overwritting existing) - which is enough for  [Shaarlier Android app](https://github.com/dimtion/Shaarlier/) to work properly (with the exception of lookup of existing bookmarks).

    export LINKDING_TOKEN=secret  # REST API key/token from http://LinkDingServer/settings/integrations
    export LINKDING_URI=http://LinkDingServer  # etc.
    python shaarli2linkding_proxy.py


## Testing

Testing with https://github.com/shaarli/python-shaarli-client, note examples
below require https://github.com/clach04/python-shaarli-client/tree/callable_module
See https://github.com/shaarli/python-shaarli-client/pull/59

    python -m shaarli_client.main -u http://localhost:8000 --secret SECRET get-info

    # below require editing shaarli_client.ini - see https://python-shaarli-client.readthedocs.io/en/latest/user/configuration.html
    python -m shaarli_client.main  get-info
    python -m shaarli_client.main  get-tags

    python -m shaarli_client.main  get-links
    python -m shaarli_client.main  get-links --searchterm hello
    python -m shaarli_client.main  get-links --searchterm hello --limit 2

    python -m shaarli_client.main  post-link --title title --url http://something.com --description "cool stuff"
    python -m shaarli_client.main  put-link --title title --url http://something.com 345

