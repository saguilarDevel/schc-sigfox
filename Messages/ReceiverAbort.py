from Messages.ACK import ACK
from Messages.Header import Header
from function import bitstring_to_bytes

class ReceiverAbort(ACK):

    def __init__(self, profile, header):
        rule_id = header.RULE_ID
        dtag = header.DTAG
        w = header.W

        header = Header(profile=profile,
                        rule_id=rule_id,
                        dtag=dtag,
                        w=w,
                        fcn='',
                        c='1')
        self.header = header
        padding = ''
        self.padding = padding
        # if the Header does not end at an L2 Word boundary,
        # append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(header.string + padding) % profile.L2_WORD_SIZE != 0:
            padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        padding += '1' * profile.L2_WORD_SIZE

        #must check this method
        # sigfox ACK must be of downlink MTU size
        while len(header.string + padding) < profile.DOWNLINK_MTU:
            padding += '1'

        super().__init__(profile, rule_id, dtag, w, c='1', bitmap='', padding=padding)


    def to_string(self):
        return self.header + self.padding

    def to_bytes(self):
        return bitstring_to_bytes(self.header + self.padding)

    def length(self):
        return len(self.header + self.padding)
