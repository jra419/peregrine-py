from scapy.all import Packet, IntField, ByteField, LongField, Emph, SourceIPField


class WhisperPeregrineHdr(Packet):
    name = 'peregrine'
    fields_desc = [Emph(SourceIPField('ip_src', 0)),
                   ByteField('ip_proto', 0),
                   IntField('length', 0),
                   LongField('timestamp', 0)]
