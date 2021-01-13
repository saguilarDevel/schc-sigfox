import unittest

from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from function import bitstring_to_bytes


class TestFragment(unittest.TestCase):
    def test_is_all_0(self):
        profile = Sigfox("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_0())

    def test_is_all_1(self):
        profile = Sigfox("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0"*profile.RULE_ID_SIZE
        dtag = "0"*profile.T
        w = "0"*profile.M
        fcn = "1" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_1())


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
        self.assertEqual(abort.header.RULE_ID, fragment.header.RULE_ID)
        self.assertEqual(abort.header.DTAG, fragment.header.DTAG)
        self.assertEqual(abort.header.W, fragment.header.W)
        self.assertTrue(abort.header.FCN[0] == '1' and all(abort.header.FCN),
                        msg=f"{abort.header.FCN[0] == '1'} and {all(abort.header.FCN)}")
        self.assertTrue(abort.payload.decode()[0] == '0' and all(abort.payload.decode()),
                        msg=f"{abort.payload[0] == '0'} and {all(abort.payload)}")
        self.assertFalse(abort.is_all_1())
        self.assertTrue(abort.is_sender_abort())


if __name__ == '__main__':
    unittest.main()
