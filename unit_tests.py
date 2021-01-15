import unittest

from Entities.Sigfox import Sigfox
from Messages.ACK import ACK
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
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
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
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


class TestReceiverAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = Sigfox("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = ReceiverAbort(profile, fragment.header)

        self.assertEqual(type(abort.profile), Sigfox)
        self.assertEqual(abort.rule_id, fragment.header.RULE_ID)
        self.assertEqual(abort.dtag, fragment.header.DTAG)
        self.assertEqual(abort.w, fragment.header.W)
        self.assertTrue(issubclass(type(abort), ACK))
        self.assertTrue(abort.is_receiver_abort())

    def test_receive(self):
        profile = Sigfox("UPLINK", "ACK ON ERROR", 1)
        ack = "000011111111111110000000000000000000000000000000000000000000000000000000000000000000000000000000"
        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        received_ack = ACK(profile,
                           rule_id=ack[:ack_index_dtag],
                           dtag=ack[ack_index_dtag:ack_index_w],
                           w=ack[ack_index_w:ack_index_c],
                           c=ack[ack_index_c],
                           bitmap=ack[ack_index_bitmap:ack_index_padding],
                           padding=ack[ack_index_padding:])

        self.assertTrue(received_ack.is_receiver_abort())


if __name__ == '__main__':
    unittest.main()
