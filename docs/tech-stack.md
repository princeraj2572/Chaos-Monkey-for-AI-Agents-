# Tech stack

Python 3.10+ and the standard library only, with no third-party dependencies. Tests use `unittest`, and the real model clients (OpenAI-style and Anthropic-style HTTP calls) are tested with a stubbed `urllib.request.urlopen`, so the test suite never touches the network. Reports are plain HTML with inline CSS. A `Makefile` provides `make test` and `make demo`, and a `Dockerfile` is included as an optional way to run the same thing.
