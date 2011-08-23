
import os
from twisted.python import log as twisted_log
from allmydata.util import base32

class FileProhibited(Exception):
    """This client has been configured to prohibit access to this object."""
    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


class Blacklist:
    def __init__(self, blacklist_filename):
        self.blacklist_filename = blacklist_filename
        self.last_mtime = None
        self.entries = {}
        self.read_blacklist() # sets .last_mtime and .entries

    def read_blacklist(self):
        try:
            current_mtime = os.stat(self.blacklist_filename).st_mtime
        except EnvironmentError:
            # unreadable blacklist file means no blacklist
            self.entries.clear()
            return
        try:
            if self.last_mtime is None or current_mtime > self.last_mtime:
                self.entries.clear()
                for line in open(self.blacklist_filename, "r").readlines():
                    line = line.lstrip()
                    if not line or line.startswith("#"):
                        continue
                    si_s, reason = line.split(None, 1)
                    si = base32.a2b(si_s) # must be valid base32
                    self.entries[si] = reason
                self.last_mtime = current_mtime
        except Exception, e:
            twisted_log.err(e, "unparseable blacklist file")
            raise

    def get_readblocker(self, si):
        self.read_blacklist()
        reason = self.entries.get(si, None)
        if reason:
            def read_prohibited(*args, **kwargs):
                # log this to logs/twistd.log, since web logs go there too
                twisted_log.msg("blacklist prohibited access to SI %s: %s" %
                                (base32.b2a(si), reason))
                raise FileProhibited(reason)
            return read_prohibited
        return None
