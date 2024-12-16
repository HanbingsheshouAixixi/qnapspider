# errors.py

class QuickConnectError(Exception):
    """Base class for QuickConnect exceptions."""
    pass


class TimeoutError(QuickConnectError):
    """Exception raised when an operation times out."""
    pass


class CancelledError(QuickConnectError):
    """Exception raised when an operation is cancelled."""
    pass


class InvalidIDError(QuickConnectError):
    """Exception raised when an invalid server ID is encountered."""
    pass


class CannotAccessError(QuickConnectError):
    """Exception raised when no URLs can be accessed."""
    pass


class ParseError(QuickConnectError):
    """Exception raised when there is a response parse error."""
    pass


class PingFailureError(QuickConnectError):
    """Exception raised when there is a ping response failure."""
    pass


class UnknownCommandError(QuickConnectError):
    """Exception raised for unknown commands."""
    pass


class UnknownServerTypeError(QuickConnectError):
    """Exception raised for unknown server types."""
    pass


# 具体的错误实例
ErrTimeout = TimeoutError("operation timed out")
ErrCancelled = CancelledError("operation cancelled")
ErrInvalidID = InvalidIDError("invalid server ID")
ErrCannotAccess = CannotAccessError("cannot access any URLs")
ErrParse = ParseError("response parse error")
ErrUnknownCommand = UnknownCommandError("unknown command")
ErrUnknownServerType = UnknownServerTypeError("unknown server type")
