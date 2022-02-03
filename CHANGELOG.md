# Changelog

All notable changes to discord-free-game-notifier will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## Changed

- URL is now using urlSlug instead of productSlug

## [0.2.0] - 2022-01-07

### Added

- Support for Steam games
- Updated dependencies (0 installs, 5 updates, 0 removals):
  - Updated charset-normalizer (2.0.9 -> 2.0.10)
  - Updated urllib3 (1.26.7 -> 1.26.8)
  - Updated gitpython (3.1.24 -> 3.1.25)
  - Updated requests (2.26.0 -> 2.27.1)
  - Updated types-requests (2.26.3 -> 2.27.2)

## [0.1.0] - 2022-01-03

### Added

- First release. Only supports Epic Games games.
  Uses a modified version of [slack-free-epic-games](https://github.com/andrewguest/slack-free-epic-games) to get the games.
