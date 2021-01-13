from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment
from Messages.Header import Header


class SenderAbort(Fragment):
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    padding = ''

    def __init__(self, profile, header):
        self.profile = profile
        rule_id = header.RULE_ID
        dtag = header.DTAG
        w = header.W
        fcn = "1" * profile.N

        while len(self.header.string + self.padding) < profile.MTU:
            self.padding += '0'

        super().__init__(profile, rule_id + dtag + w + fcn + self.padding)
