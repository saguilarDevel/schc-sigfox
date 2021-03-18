class SCHCError(Exception):
    pass


class LengthMismatchError(SCHCError):
    pass


class SCHCTimeoutError(SCHCError):
    pass
