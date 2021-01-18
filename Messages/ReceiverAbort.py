from Messages.Header import Header
from function import bitstring_to_bytes

class ReceiverAbort:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    padding = ''

    def __init__(self, profile, rule_id, dtag):
        self.profile = profile
        # w should always be 1
        self.w = ''
        while len(self.w) < self.profile.M:
            self.w += '1'
        self.header = Header(profile=profile,
                             rule_id=rule_id,
                             dtag=dtag,
                             w=self.w,
                             fcn='',
                             c='1')

        # if the Header does not end at an L2 Word boundary, append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(self.header.string + self.padding) % profile.L2_WORD_SIZE != 0:
            self.padding += '1'
        # if the Header does not end at an L2 Word boundary, append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(self.header.string + self.padding) % profile.L2_WORD_SIZE != 0:
            self.padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        self.padding += '1'*profile.L2_WORD_SIZE
        # sigfox ACK must be of downlink MTU size
        while len(self.header.string + self.padding) < profile.MTU:
            self.padding += '1'

    def to_string(self):
        return self.header.string + self.padding

    def to_bytes(self):
        return bitstring_to_bytes(self.header.string + self.padding)

    def length(self):
        return len(self.header + self.padding)
