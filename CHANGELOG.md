# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2024-06-12
### Fixed
- FileFaker crashed when relative path was used

## [2.1.0] - 2024-06-07
### Added
- Make it possible to use Pathlib.Path in FileFaker

## [2.0.0] - 2024-05-31
### Removed
- TOS 3.X related code and files

## [1.0.2] - 2024-02-27
### Fixed
- API updated for loop_stop in paho-mqtt

## [1.0.1] - 2024-02-27
### Fixed
- make it compatibility with paho-mqtt 2.X

## [1.0.0] - 2024-02-02
### Added
- wwan tarball (omnia) for LTE testing

### Changed
- build project using hatchling

## [0.16.0] - 2023-10-12
### Added
- export all fixtures as a part of pytest plugin

## [0.15.0] - 2023-10-02
### Added
- Add mock for Turris 1.1 with QMI modems on TOS 7.0
- Add mock for Mox ABC with QMI modems on TOS 7.0
- Backport mock for Omnia with VLANs on Turris OS 6.0

### Changed
- Update default mock for Mox AEEC on TOS 7.0
- Update default mock for Turris 1.x on TOS 7.0
- Update default mock for Omnia on TOS 7.0

## [0.14.1] - 2023-08-03
### Added
- setup.py: aviod using git dependencies of foris-controller

## [0.14.0] - 2023-06-29
### Added
- building and publishing python package using gitlab CI

## [0.13.0] - 2023-02-08
### Removed
- setup.py: Drop `turrishw` from dependencies to avoid dependency conflict
  while trying to run tests from `foris-controller`.

## [0.12.0] - 2022-07-15
### Added
- updater: Add type annotations for approvals

## [0.11.0] - 2022-06-27
### Added
- add mock for TOS 6.0 on Turris 1.x routers

### Changed
- utils: Refactor `prepare_turrishw_root` function for better HW mocks lookup.

## [0.10.1] - 2021-08-25
### Fixed
- waiting mqtt bus failed in some CI setups

## [0.10.0] - 2021-07-20
### Added
- add `read_and_parse_file` function (reads and parses a content of the file by regex)

## [0.9.0] - 2021-07-02
### Added
- add mock for TOS 5.2.0 on Turris 1.x routers

### Changed
- svupdater: replace Nikola with FWLogs in package lists
- migrate CHANGELOG to Keep a Changelog style

## [0.8.0] - 2021-04-08

- svupdater package list updates and fixes
- cmdline_file fixture added
- prepare_turrishw fixture added
- fix wait for file / port to be opened before foris-controller is started
- utils: run generic command
- better error message for incorrect backend

## [0.7] - 2020-05-13

- deprecation of start_buses, ubusd_test, mosquitto_test fixture
- infrastructure refactored
- infrastructure handlers starting and stopping of message buses

## [0.6] - 2020-04-15

- use it as pytest plugin
- register markers
- reflect svupdater updates
- sleep when mqtt socket is not available
- update repository urls
- add env_overrides fixture
- reformat code using black
- lighttpd restart command
- add delay to reboot_was_called and network_restart_was_called
- mqtt fixes and updates

## [0.5] - 2018-12-21

- fix env variables handling
- make message bus configurable via cmdline
- ubusd_acl support removed
- mqtt bus support added
- mocked updater changes
- use PEP508 dependencies
- check_service_result updated
- device and turris_os_version parametrized fixtures added
- turrishw integration
- newtwork_restart and reboot fixtures added
- python3 compatibility fixes
- FileFaker class added
- notify api added

## [0.4] - 2018-06-19

- reflect foris-schema api update
- ubus: message format update
- get_uci_module function added
- mocked update: reflect api changes
- infrastructure: filters for get_notifications
- client socket: integrate to infrastructure
- client socket: more modular
- mocked updater: more functions and fuctionality added
- client socket: debug output fix

## [0.3] - 2018-02-27

- sending requests and notifications via client socket
- router_notifications module added to modules
- wan module added to modules
- time module added to modules

## [0.2] - 2018-01-15

- services and cmdline test helpers added
- custom path to script dirs root
- file test helpers added
- sh_was_called helper added

## [0.1] - 2018-01-08

- initial version

## [0.0] - 2018-01-08

- splitted from foris-controller (git history kept)
