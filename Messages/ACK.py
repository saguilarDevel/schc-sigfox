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

        self.header = self.rule_id + self.dtag + self.w + self.bitmap + self.c
        # print("profile.MTU / len(self.header + self.padding) -> {}".format(round(len(self.header + self.padding) / 8)))
        # while len(self.header + self.padding) < round(len(self.header + self.padding) / 8) * 8:
        while len(self.header + self.padding) < profile.MTU:
            self.padding += '1'

    def to_string(self):
        return self.header + self.padding

    def to_bytes(self):
        return self.bitstring_to_bytes(self.header + self.padding)

    def length(self):
        return len(self.header + self.padding)

    def bitstring_to_bytes(self, s):
        return int(s, 2).to_bytes(len(s) // 8, byteorder='big')
