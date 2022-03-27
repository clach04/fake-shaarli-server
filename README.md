# fake-shaarli-server

Python implementation of _some_ of the [Shaarli REST API](http://shaarli.github.io/api-documentation/)

Just enough to convince the [Shaarlier Android app](https://github.com/dimtion/Shaarlier/) it's a real server.
Also (partially) works with [python-shaarli-client](https://github.com/shaarli/python-shaarli-client).

This doesn't actual do anything and is essentially non-functional. It completely ignores security (JWT) tokens (it does not handle the deprecated username/password authentication option). Basicallty, don't use it ;) Use https://github.com/shaarli/Shaarli instead :)
