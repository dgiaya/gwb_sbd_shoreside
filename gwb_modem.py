
from acomms import Micromodem


class GWBModem(Micromodem):

    def __init__(self, name='modem', unified_log=None, log_path=None, log_level='INFO'):
        super(GWBModem, self).__init__(name=name, unified_log=unified_log, log_path=log_path, log_level=log_level)

        self.rxframe_listeners.append(self.append_incoming_frame)
        self.cst_listeners.append(self.received_cst)

        self.packetdata = bytearray()

        self.packet_listeners = []

    def append_incoming_frame(self, frame):
        if frame is not None:
            self.packetdata = self.packetdata + frame.data

    def received_cst(self, cst, msg):
        # Check that we were expecting frames with this reception and that they
        # all passed the CRC check
        if (cst.get('num_frames') > 0) and (cst.get('bad_frames_num') == 0):
            if len(self.packetdata) > 0:
                print(self.packetdata.hex())
                for func in self.packet_listeners:
                    func(self.packetdata)

        # Clear out the packet data
        self.packetdata = bytearray()
