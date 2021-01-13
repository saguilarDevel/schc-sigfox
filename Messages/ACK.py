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

    def __init__(self, profile, rule_id, dtag, w, bitmap, c):
        self.profile = profile
        self.rule_id = rule_id
        self.dtag = dtag
        self.w = w
        self.bitmap = bitmap
        self.c = c

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
