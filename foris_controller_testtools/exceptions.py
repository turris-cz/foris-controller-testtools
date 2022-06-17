class ForisControllerTesttoolsError(Exception):
    pass

class BackendNotImplementedError(ForisControllerTesttoolsError):
    pass

class MockNotFoundError(ForisControllerTesttoolsError):
    pass
