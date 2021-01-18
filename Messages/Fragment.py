from Messages.Header import Header
from function import bitstring_to_bytes, zfill, is_monochar

class Fragment:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    payload = None

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

    def test(self):
        print("Header: " + self.header.string)
        print("Payload: " + str(self.payload))

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

    def is_sender_abort(self):
        fcn = self.header.FCN
        padding = self.payload.decode()
        print('padding:{}'.format(padding))
        print('fcn[0] == 1: {}'.format(fcn[0] == '1'))
        print('is_monochar(fcn): {}'.format(is_monochar(fcn)))
        print('padding[0]: {}'.format(padding[0]))
        print('is_monochar(padding): {}'.format(is_monochar(padding)))
        print('1 not in padding: {}'.format('1' in padding))
        # return fcn[0] == '1' and is_monochar(fcn) and padding[0] == '0' and is_monochar(padding)
        return fcn[0] == '1' and is_monochar(fcn) and '1' not in padding
