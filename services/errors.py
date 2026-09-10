"""Exceções do pipeline com mensagem amigável para a interface."""


class AnalyzerError(Exception):
    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class NotGitHubError(AnalyzerError):
    pass


class InvalidUrlError(AnalyzerError):
    pass


class RepoTooLargeError(AnalyzerError):
    pass


class CloneError(AnalyzerError):
    pass


class CloneTimeoutError(AnalyzerError):
    pass


class EmptyRepositoryError(AnalyzerError):
    pass


class InvalidDateError(AnalyzerError):
    pass

