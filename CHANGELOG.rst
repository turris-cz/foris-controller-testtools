0.6 (2020-04-15)
----------------

* use it as pytest plugin
* register markers
* reflect svupdater updates
* sleep when mqtt socket is not available
* update repository urls
* add env_overrides fixture
* reformat code using black
* lighttpd restart command
* add delay to reboot_was_called and network_restart_was_called
* mqtt fixes and updates

0.5 (2018-12-21)
----------------

* fix env variables handling
* make message bus configurable via cmdline
* ubusd_acl support removed
* mqtt bus support added
* mocked updater changes
* use PEP508 dependencies
* check_service_result updated
* device and turris_os_version parametrized fixtures added
* turrishw integration
* newtwork_restart and reboot fixtures added
* python3 compatibility fixes
* FileFaker class added
* notify api added

0.4 (2018-06-19)
----------------

* reflect foris-schema api update
* ubus: message format update
* get_uci_module function added
* mocked update: reflect api changes
* infrastructure: filters for get_notifications
* client socket: integrate to infrastructure
* client socket: more modular
* mocked updater: more functions and fuctionality added
* client socket: debug output fix

0.3 (2018-02-27)
----------------

* sending requests and notifications via client socket
* router_notifications module added to modules
* wan module added to modules
* time module added to modules

0.2 (2018-01-15)
----------------

* services and cmdline test helpers added
* custom path to script dirs root
* file test helpers added
* sh_was_called helper added

0.1 (2018-01-08)
----------------

* initial version

0.0 (2018-01-08)
----------------

* splitted from foris-controller (git history kept)
