Changelog
=========

0.4
---

- Add support for the HyBi version of WebSockets (specifically version-10). This version was released to solve some previous security concerns and
will be the version in Firefox 7/8 and Chrome 14 onwards accoring to Wikipedia.
- Introduces a dependency on ws4py

- See http://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-10

0.3
---

- Fix bug in setup.py
- Improve documentation and consistency with pyramid naming

0.2
---

- Support for version 76 of the websocket handshake

0.1
---

- Initial release, ported from rpz.websocket and repoze.bfg to pyramid
