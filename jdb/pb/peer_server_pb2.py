# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: peer_server.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='peer_server.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n\x11peer_server.proto\"\xea\x01\n\x0fMembershipState\x12\x12\n\nreplica_id\x18\x01 \x01(\r\x12-\n\x07\x61\x64\x64_set\x18\x02 \x03(\x0b\x32\x1c.MembershipState.AddSetEntry\x12\x33\n\nremove_set\x18\x03 \x03(\x0b\x32\x1f.MembershipState.RemoveSetEntry\x1a-\n\x0b\x41\x64\x64SetEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x02:\x02\x38\x01\x1a\x30\n\x0eRemoveSetEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x02:\x02\x38\x01\"\x07\n\x05\x45mpty2m\n\nPeerServer\x12;\n\x13MembershipStateSync\x12\x10.MembershipState\x1a\x10.MembershipState\"\x00\x12\"\n\x0eMembershipPing\x12\x06.Empty\x1a\x06.Empty\"\x00\x62\x06proto3'
)




_MEMBERSHIPSTATE_ADDSETENTRY = _descriptor.Descriptor(
  name='AddSetEntry',
  full_name='MembershipState.AddSetEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='MembershipState.AddSetEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='MembershipState.AddSetEntry.value', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=161,
  serialized_end=206,
)

_MEMBERSHIPSTATE_REMOVESETENTRY = _descriptor.Descriptor(
  name='RemoveSetEntry',
  full_name='MembershipState.RemoveSetEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='MembershipState.RemoveSetEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='MembershipState.RemoveSetEntry.value', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=208,
  serialized_end=256,
)

_MEMBERSHIPSTATE = _descriptor.Descriptor(
  name='MembershipState',
  full_name='MembershipState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='replica_id', full_name='MembershipState.replica_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='add_set', full_name='MembershipState.add_set', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='remove_set', full_name='MembershipState.remove_set', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_MEMBERSHIPSTATE_ADDSETENTRY, _MEMBERSHIPSTATE_REMOVESETENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=256,
)


_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=258,
  serialized_end=265,
)

_MEMBERSHIPSTATE_ADDSETENTRY.containing_type = _MEMBERSHIPSTATE
_MEMBERSHIPSTATE_REMOVESETENTRY.containing_type = _MEMBERSHIPSTATE
_MEMBERSHIPSTATE.fields_by_name['add_set'].message_type = _MEMBERSHIPSTATE_ADDSETENTRY
_MEMBERSHIPSTATE.fields_by_name['remove_set'].message_type = _MEMBERSHIPSTATE_REMOVESETENTRY
DESCRIPTOR.message_types_by_name['MembershipState'] = _MEMBERSHIPSTATE
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MembershipState = _reflection.GeneratedProtocolMessageType('MembershipState', (_message.Message,), {

  'AddSetEntry' : _reflection.GeneratedProtocolMessageType('AddSetEntry', (_message.Message,), {
    'DESCRIPTOR' : _MEMBERSHIPSTATE_ADDSETENTRY,
    '__module__' : 'peer_server_pb2'
    # @@protoc_insertion_point(class_scope:MembershipState.AddSetEntry)
    })
  ,

  'RemoveSetEntry' : _reflection.GeneratedProtocolMessageType('RemoveSetEntry', (_message.Message,), {
    'DESCRIPTOR' : _MEMBERSHIPSTATE_REMOVESETENTRY,
    '__module__' : 'peer_server_pb2'
    # @@protoc_insertion_point(class_scope:MembershipState.RemoveSetEntry)
    })
  ,
  'DESCRIPTOR' : _MEMBERSHIPSTATE,
  '__module__' : 'peer_server_pb2'
  # @@protoc_insertion_point(class_scope:MembershipState)
  })
_sym_db.RegisterMessage(MembershipState)
_sym_db.RegisterMessage(MembershipState.AddSetEntry)
_sym_db.RegisterMessage(MembershipState.RemoveSetEntry)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'peer_server_pb2'
  # @@protoc_insertion_point(class_scope:Empty)
  })
_sym_db.RegisterMessage(Empty)


_MEMBERSHIPSTATE_ADDSETENTRY._options = None
_MEMBERSHIPSTATE_REMOVESETENTRY._options = None

_PEERSERVER = _descriptor.ServiceDescriptor(
  name='PeerServer',
  full_name='PeerServer',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=267,
  serialized_end=376,
  methods=[
  _descriptor.MethodDescriptor(
    name='MembershipStateSync',
    full_name='PeerServer.MembershipStateSync',
    index=0,
    containing_service=None,
    input_type=_MEMBERSHIPSTATE,
    output_type=_MEMBERSHIPSTATE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='MembershipPing',
    full_name='PeerServer.MembershipPing',
    index=1,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_EMPTY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_PEERSERVER)

DESCRIPTOR.services_by_name['PeerServer'] = _PEERSERVER

# @@protoc_insertion_point(module_scope)
