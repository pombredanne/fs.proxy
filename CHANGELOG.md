# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.1.3] - 2017-08-16
### Fixed
- Bad version specifier for `fs` dependency
### Removed
- Redundant definition of the `fs.proxy.writer.ProxyWriter.validatepath`

## [v0.1.2] - 2017-07-03
### Added
- Examples to README.rst
### Fixed
- Wrong super() argument in fs.proxy.writer
- fs.proxy._utils.__all__ containing an undefined name cause by
  renaming of `unique_everseen` to unique
- tested example in README.md failing in Python 2
- requirements not installing on a wheel install

## [v0.1.1] - 2017-06-29
### Fixed
- Wrong readme name causing setuptools to ignore the actual readme

## v0.1.0 - 2017-06-29
### Added
- README, COPYING and CHANGELOG files
- configuration for Travis-CI
- `setup.py` file configured with `setup.cfg` (requires setuptools)
- Base proxy classes in `fs.proxy.base`
- Writer proxy classes in `fs.proxy.writer`, making read-only filesystem
writeable through a proxy filesystem

[Unreleased]: https://github.com/althonos/fs.proxy/compare/v0.1.3...HEAD
[vO.1.3]: https://github.com/althonos/fs.proxy/compare/v0.1.2...v0.1.3
[vO.1.2]: https://github.com/althonos/fs.proxy/compare/v0.1.1...v0.1.2
[vO.1.1]: https://github.com/althonos/fs.proxy/compare/v0.1.0...v0.1.1
