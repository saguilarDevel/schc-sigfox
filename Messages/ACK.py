from function import bitstring_to_bytes


class ACK:

    profile = None
    rule_id = None
    dtag = None
    w = None
    bitmap = None
    c = None
    header = ''
    padding = ''

    def __init__(self, profile, rule_id, dtag, w, c, bitmap, padding=''):
        self.profile = profile
        self.rule_id = rule_id
        self.dtag = dtag
        self.w = w
        self.c = c
        self.bitmap = bitmap
        self.padding = padding

        if self.c == "1":
            self.header = self.rule_id + self.dtag + self.w + self.c
        else:
            self.header = self.rule_id + self.dtag + self.w + self.c + self.bitmap
        while len(self.header + self.padding) < profile.MTU:
            self.padding += '0'

    def to_string(self):
        return self.header + self.padding

    def to_bytes(self):
        return bitstring_to_bytes(self.header + self.padding)

    def length(self):
        return len(self.header + self.padding)

    def is_receiver_abort(self):
        ack_string = self.to_string()
        l2_word_size = self.profile.L2_WORD_SIZE
        start = ack_string[:-l2_word_size]
        header = ack_string[:len(self.rule_id + self.dtag + self.w + self.c)]
        padding_start = start[len(self.rule_id + self.dtag + self.w + self.c):-l2_word_size]
        padding_end = ack_string[-l2_word_size:]
        if padding_end == "1"*l2_word_size:
            if padding_start != '' and len(header) % l2_word_size != 0:
                return len(header) % l2_word_size != 0 and padding_start.is_monochar() and padding_start[0] == 1
            else:
                return len(header) % l2_word_size == 0
        else:
            return False
