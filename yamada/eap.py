import struct
import random

from ryu.lib import stringify
from ryu.lib.packet import packet_base

EAP_CODE_REQUEST = 0x01
EAP_CODE_RESPONSE = 0x02
EAP_CODE_SUCCESS = 0x03
EAP_CODE_FAILURE = 0x04

EAP_TYPE_IDENTIFY = 0x01
EAP_TYPE_MD5_CHALLENGE = 0x04


class eap(packet_base.PacketBase):
    _PACK_STR = "!BBH"
    _TYPE_PACK_STR = "!B"
    _MIN_LEN = struct.calcsize(_PACK_STR)
    _TYPE_LEN = struct.calcsize(_TYPE_PACK_STR)
    _EAP_TYPES = {}

    @staticmethod
    def register_eap_type(*args):
        def _register_eap_type(cls):
            for type_ in args:
                eap._EAP_TYPES[type_] = cls
            return cls
        return _register_eap_type

    def __init__(self, code=EAP_CODE_SUCCESS, identifier=None, length=0,
                 type_=None, data=None):
        super(eap, self).__init__()
        self.code = code
        self.length = length
        self.type_ = type_
        self.data = data

        if identifier is None:
            self.identifier = random.randint(0x00, 0xff)
        else:
            self.identifier = identifier

    def __len__(self):
        return self.length

    @classmethod
    def parser(cls, buf):
        (code, identifier, length) = struct.unpack_from(cls._PACK_STR, buf)
        msg = cls(code, identifier, length)

        if code in [EAP_CODE_REQUEST, EAP_CODE_RESPONSE]:
            offset = eap._MIN_LEN
            type_buf = buf[offset:offset+eap._TYPE_LEN]
            type_ = struct.unpack_from(eap._TYPE_PACK_STR, type_buf)[0]
            msg.type_ = type_

            offset += eap._TYPE_LEN
            type_data_size = length - eap._MIN_LEN - eap._TYPE_LEN
            type_data_buf = buf[offset:offset+type_data_size]
            cls_ = eap._EAP_TYPES.get(type_, None)
            if cls_:
                msg.data = cls_.parser(type_data_buf)
            else:
                msg.data = type_data_buf

        return msg, None, None

    def serialize(self, payload, prev):
        if self.length == 0:
            self.length = eap._MIN_LEN
            if self.code in [EAP_CODE_REQUEST, EAP_CODE_RESPONSE]:
                if self.data is not None:
                    self.length += len(self.data)

        hdr = bytearray(struct.pack(self._PACK_STR, self.code, self.identifier,
                        self.length))
        if self.code in [EAP_CODE_REQUEST, EAP_CODE_RESPONSE]:
            hdr += bytearray(struct.pack(eap._TYPE_PACK_STR, self.type_))
            if self.data is not None:
                if self.type_ in eap._EAP_TYPES:
                    hdr += self.data.serialize()
                else:
                    hdr += self.data

        return hdr


@eap.register_eap_type(EAP_TYPE_IDENTIFY)
class eap_identify(stringify.StringifyMixin):
    def __init__(self, identity=""):
        super(eap_identify, self).__init__()
        self.identity = identity

    def __len__(self):
        return len(self.identity)

    @classmethod
    def parser(cls, buf):
        return cls(buf.decode("utf-8"))

    def serialize(self):
        hdr = bytearray(self.identity.encode("utf-8"))
        return hdr
