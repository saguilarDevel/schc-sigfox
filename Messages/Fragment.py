from Messages.Header import Header
from function import bitstring_to_bytes


def zfill(string, width):
    if len(string) < width:
        return ("0" * (width - len(string))) + string
    else:
        return string


class Fragment:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    payload = None
    string = ''

    def __init__(self, profile, fragment):
        self.profile = profile

        self.header_length = profile.HEADER_LENGTH
        self.rule_id_size = profile.RULE_ID_SIZE
        self.t = profile.T
        self.n = profile.N
        self.m = profile.M

        header = zfill(str(bin(int.from_bytes(fragment[0], 'big')))[2:], self.header_length)
        payload = fragment[1]

        rule_id = str(header[:self.rule_id_size])
        dtag = str(header[self.rule_id_size:self.rule_id_size + self.t])
        window = str(header[self.rule_id_size + self.t:self.rule_id_size + self.t + self.m])
        fcn = str(header[self.rule_id_size + self.t + self.m:self.rule_id_size + self.t + self.m + self.n])
        c = ""

        self.header = Header(self.profile, rule_id, dtag, window, fcn, c)
        self.payload = payload
        self.bytes = self.header.bytes + self.payload
        self.string = self.bytes.decode()
        self.hex = self.bytes.hex()

    def test(self):
        print(f"Header: {self.header.string}")
        print(f"Payload: {str(self.payload)}")
        print(f"String: {self.string}")
        print(f"Bytes: {self.bytes}")
        print(f"Hex: {self.hex}")

    def is_all_1(self):
        fcn = self.header.FCN
        fcn_set = set()
        for x in fcn:
            fcn_set.add(x)
        return len(fcn_set) == 1 and "1" in fcn_set

    def is_all_0(self):
        fcn = self.header.FCN
        fcn_set = set()
        for x in fcn:
            fcn_set.add(x)
        return len(fcn_set) == 1 and "0" in fcn_set

    def expects_ack(self):
        return self.is_all_0() or self.is_all_1()
