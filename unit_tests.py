import unittest

from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort


class TestSenderAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = Sigfox("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = SenderAbort(profile, fragment.header)

        self.assertEqual(type(abort.profile), Sigfox)
        self.assertEqual(type(abort.header.RULE_ID), fragment.header.RULE_ID)
        self.assertEqual(type(abort.header.DTAG), fragment.header.DTAG)
        self.assertEqual(type(abort.header.W), fragment.header.W)
        self.assertTrue(abort.header.FCN[0] == '1' and all(abort.header.FCN))
        self.assertTrue(abort.payload[0] == '0' and all(abort.payload))


if __name__ == '__main__':
    unittest.main()
