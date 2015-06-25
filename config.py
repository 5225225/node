MINUTES = 60
HOURS = MINUTES * 60
DAYS = HOURS * 24
WEEKS = DAYS * 7
YEARS = DAYS * 365

# Allows you to do `3 * DAYS` to make configuration clearer.
# Technically the value for YEARS is wrong, but it's close enough.

POW_DIGITS = 2

PROTOCOL_VERSION = b"0xdeadbeef"
assert len(PROTOCOL_VERSION) <= 16
PROTOCOL_VERSION = (bytes(16) + PROTOCOL_VERSION)[-16:]

PORT = 3514
BROADPORT = 5252
VERBOSE = False

MSGDIR = "msgs/"
LISTEN_FOR_BROADCASTS = True
CREATE_BROADCASTS = True

PRUNE_TIME = 7 * DAYS
PRUNE_DELETE = True

USE_GETTEXT = False
