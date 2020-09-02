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

        while len(self.header + self.padding) < profile.MTU:
            self.padding += '1'

    def to_string(self):
        return self.header + self.padding
