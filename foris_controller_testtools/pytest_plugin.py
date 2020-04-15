import pytest  # noqa


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "only_backends([backend, ...]): run only on a limited set of backends",
    )
    config.addinivalue_line(
        "markers", "only_message_buses([bus, ...]): run only on a limited set of message buses",
    )
    config.addinivalue_line(
        "markers", "uci_config_path(path): set path to uci configs used for the tests",
    )
    config.addinivalue_line(
        "markers", "file_root_path(path): set path to mock file system root",
    )
