"""Exceptions for errors raised by local backend."""

class QuTrunkError(Exception):
    """Base class for errors raised by QuTrunk."""

    def __init__(self, *message):
        """Set the error message.

        Args:
            message: Error message.
        """
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class LocalBackendError(QuTrunkError):
    """Base class for errors raised by Local backend."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(*message)
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)
