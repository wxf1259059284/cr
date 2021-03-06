# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ad_behavior.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import sisdk.libad.base_pb2 as base__pb2
import sisdk.libad.ad_enum_pb2 as ad__enum__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='ad_behavior.proto',
  package='ad_behavior',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x11\x61\x64_behavior.proto\x12\x0b\x61\x64_behavior\x1a\nbase.proto\x1a\rad_enum.proto\"s\n\nad_damages\x12\x10\n\x08occupied\x18\x01 \x01(\x08\x12\x0b\n\x03pwn\x18\x02 \x01(\x08\x12\x0c\n\x04\x64own\x18\x03 \x01(\x08\x12\x0f\n\x07team_id\x18\x04 \x01(\t\x12\x0f\n\x07unit_id\x18\x05 \x01(\t\x12\x16\n\x0eresult_damages\x18\x06 \x01(\x08\"\xf0\x01\n\x07\x61\x64_unit\x12\n\n\x02id\x18\x01 \x01(\t\x12.\n\x0b\x64\x65vice_type\x18\x02 \x01(\x0e\x32\x19.ad_enum.enum_device_type\x12\x34\n\nmodel_type\x18\x03 \x01(\x0e\x32 .ad_enum.enum_virtual_model_type\x12\r\n\x05\x63olor\x18\x04 \x01(\t\x12\x15\n\rshow_children\x18\x05 \x01(\x08\x12(\n\x07\x64\x61mages\x18\x06 \x01(\x0b\x32\x17.ad_behavior.ad_damages\x12#\n\x05units\x18\x07 \x03(\x0b\x32\x14.ad_behavior.ad_unit\"t\n\x07\x61\x64_team\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\r\n\x05\x63olor\x18\x03 \x01(\t\x12\r\n\x05score\x18\x04 \x01(\x05\x12#\n\x05units\x18\x05 \x03(\x0b\x32\x14.ad_behavior.ad_unit\x12\x0c\n\x04logo\x18\x08 \x01(\t\"\x81\x01\n\tad_puzzle\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x12\n\ntitle_type\x18\x03 \x01(\t\x12\x13\n\x0btitle_score\x18\x04 \x01(\x05\x12\x0b\n\x03tag\x18\x05 \x01(\t\x12\x0e\n\x06solved\x18\x06 \x01(\x05\x12\x14\n\x0cpuzzle_count\x18\x07 \x01(\x05\"c\n\x07\x61\x64_init\x12)\n\x0bteam_entity\x18\x01 \x03(\x0b\x32\x14.ad_behavior.ad_team\x12-\n\rpuzzle_entity\x18\x02 \x03(\x0b\x32\x16.ad_behavior.ad_puzzle\"\xcd\x02\n\tad_attack\x12\x31\n\tintensity\x18\x01 \x01(\x0e\x32\x1e.ad_enum.enum_attack_intensity\x12\x13\n\x0bsrc_team_id\x18\x02 \x01(\t\x12\x13\n\x0bsrc_unit_id\x18\x03 \x01(\t\x12\'\n\x05\x63olor\x18\x04 \x01(\x0e\x32\x18.ad_enum.enum_color_type\x12\x14\n\x0c\x64\x65st_team_id\x18\x05 \x01(\t\x12\x14\n\x0c\x64\x65st_unit_id\x18\x06 \x01(\t\x12\x11\n\tis_puzzle\x18\x07 \x01(\x08\x12\x15\n\ris_firstblood\x18\x08 \x01(\x08\x12\x13\n\x0bis_defensed\x18\t \x01(\x08\x12\x11\n\tsrc_score\x18\n \x01(\x02\x12\x12\n\ndest_score\x18\x0b \x01(\x02\x12(\n\x07\x64\x61mages\x18\x0c \x01(\x0b\x32\x17.ad_behavior.ad_damages\"R\n\x14\x61\x64_team_score_aciton\x12\x0f\n\x07team_id\x18\x01 \x01(\t\x12\x15\n\rteam_child_id\x18\x02 \x01(\t\x12\x12\n\nteam_score\x18\x05 \x01(\x05\"\x8f\x01\n\x0f\x61\x64_entity_panel\x12\x12\n\nsrc_obj_id\x18\x01 \x01(\t\x12!\n\x06switch\x18\x02 \x01(\x0e\x32\x11.base.enum_on_off\x12\x12\n\nip_address\x18\x03 \x01(\t\x12\x0f\n\x07os_name\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\t\x12\x10\n\x08\x64uration\x18\x06 \x01(\x05\"\xce\x01\n\tad_effect\x12!\n\x06switch\x18\x01 \x01(\x0e\x32\x11.base.enum_on_off\x12\'\n\x06\x65\x66\x66\x65\x63t\x18\x02 \x01(\x0e\x32\x17.ad_enum.enum_ad_effect\x12\x12\n\nsrc_obj_id\x18\x03 \x01(\t\x12\x0f\n\x07team_id\x18\x04 \x01(\t\x12\x15\n\rteam_child_id\x18\x05 \x01(\t\x12\'\n\x05\x63olor\x18\x06 \x01(\x0e\x32\x18.ad_enum.enum_color_type\x12\x10\n\x08\x64uration\x18\x07 \x01(\x05\x62\x06proto3')
  ,
  dependencies=[base__pb2.DESCRIPTOR,ad__enum__pb2.DESCRIPTOR,])




_AD_DAMAGES = _descriptor.Descriptor(
  name='ad_damages',
  full_name='ad_behavior.ad_damages',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='occupied', full_name='ad_behavior.ad_damages.occupied', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pwn', full_name='ad_behavior.ad_damages.pwn', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='down', full_name='ad_behavior.ad_damages.down', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='team_id', full_name='ad_behavior.ad_damages.team_id', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='unit_id', full_name='ad_behavior.ad_damages.unit_id', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='result_damages', full_name='ad_behavior.ad_damages.result_damages', index=5,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=61,
  serialized_end=176,
)


_AD_UNIT = _descriptor.Descriptor(
  name='ad_unit',
  full_name='ad_behavior.ad_unit',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='ad_behavior.ad_unit.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='device_type', full_name='ad_behavior.ad_unit.device_type', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='model_type', full_name='ad_behavior.ad_unit.model_type', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='ad_behavior.ad_unit.color', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='show_children', full_name='ad_behavior.ad_unit.show_children', index=4,
      number=5, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='damages', full_name='ad_behavior.ad_unit.damages', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='units', full_name='ad_behavior.ad_unit.units', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=179,
  serialized_end=419,
)


_AD_TEAM = _descriptor.Descriptor(
  name='ad_team',
  full_name='ad_behavior.ad_team',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='ad_behavior.ad_team.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='ad_behavior.ad_team.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='ad_behavior.ad_team.color', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='score', full_name='ad_behavior.ad_team.score', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='units', full_name='ad_behavior.ad_team.units', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='logo', full_name='ad_behavior.ad_team.logo', index=5,
      number=8, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=421,
  serialized_end=537,
)


_AD_PUZZLE = _descriptor.Descriptor(
  name='ad_puzzle',
  full_name='ad_behavior.ad_puzzle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='ad_behavior.ad_puzzle.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='ad_behavior.ad_puzzle.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='title_type', full_name='ad_behavior.ad_puzzle.title_type', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='title_score', full_name='ad_behavior.ad_puzzle.title_score', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='tag', full_name='ad_behavior.ad_puzzle.tag', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='solved', full_name='ad_behavior.ad_puzzle.solved', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='puzzle_count', full_name='ad_behavior.ad_puzzle.puzzle_count', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=540,
  serialized_end=669,
)


_AD_INIT = _descriptor.Descriptor(
  name='ad_init',
  full_name='ad_behavior.ad_init',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='team_entity', full_name='ad_behavior.ad_init.team_entity', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='puzzle_entity', full_name='ad_behavior.ad_init.puzzle_entity', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=671,
  serialized_end=770,
)


_AD_ATTACK = _descriptor.Descriptor(
  name='ad_attack',
  full_name='ad_behavior.ad_attack',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='intensity', full_name='ad_behavior.ad_attack.intensity', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_team_id', full_name='ad_behavior.ad_attack.src_team_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_unit_id', full_name='ad_behavior.ad_attack.src_unit_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='ad_behavior.ad_attack.color', index=3,
      number=4, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_team_id', full_name='ad_behavior.ad_attack.dest_team_id', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_unit_id', full_name='ad_behavior.ad_attack.dest_unit_id', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_puzzle', full_name='ad_behavior.ad_attack.is_puzzle', index=6,
      number=7, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_firstblood', full_name='ad_behavior.ad_attack.is_firstblood', index=7,
      number=8, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_defensed', full_name='ad_behavior.ad_attack.is_defensed', index=8,
      number=9, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_score', full_name='ad_behavior.ad_attack.src_score', index=9,
      number=10, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_score', full_name='ad_behavior.ad_attack.dest_score', index=10,
      number=11, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='damages', full_name='ad_behavior.ad_attack.damages', index=11,
      number=12, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=773,
  serialized_end=1106,
)


_AD_TEAM_SCORE_ACITON = _descriptor.Descriptor(
  name='ad_team_score_aciton',
  full_name='ad_behavior.ad_team_score_aciton',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='team_id', full_name='ad_behavior.ad_team_score_aciton.team_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='team_child_id', full_name='ad_behavior.ad_team_score_aciton.team_child_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='team_score', full_name='ad_behavior.ad_team_score_aciton.team_score', index=2,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=1108,
  serialized_end=1190,
)


_AD_ENTITY_PANEL = _descriptor.Descriptor(
  name='ad_entity_panel',
  full_name='ad_behavior.ad_entity_panel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='ad_behavior.ad_entity_panel.src_obj_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch', full_name='ad_behavior.ad_entity_panel.switch', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ip_address', full_name='ad_behavior.ad_entity_panel.ip_address', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='os_name', full_name='ad_behavior.ad_entity_panel.os_name', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='status', full_name='ad_behavior.ad_entity_panel.status', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='ad_behavior.ad_entity_panel.duration', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=1193,
  serialized_end=1336,
)


_AD_EFFECT = _descriptor.Descriptor(
  name='ad_effect',
  full_name='ad_behavior.ad_effect',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='switch', full_name='ad_behavior.ad_effect.switch', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='effect', full_name='ad_behavior.ad_effect.effect', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='ad_behavior.ad_effect.src_obj_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='team_id', full_name='ad_behavior.ad_effect.team_id', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='team_child_id', full_name='ad_behavior.ad_effect.team_child_id', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='ad_behavior.ad_effect.color', index=5,
      number=6, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='ad_behavior.ad_effect.duration', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=1339,
  serialized_end=1545,
)

_AD_UNIT.fields_by_name['device_type'].enum_type = ad__enum__pb2._ENUM_DEVICE_TYPE
_AD_UNIT.fields_by_name['model_type'].enum_type = ad__enum__pb2._ENUM_VIRTUAL_MODEL_TYPE
_AD_UNIT.fields_by_name['damages'].message_type = _AD_DAMAGES
_AD_UNIT.fields_by_name['units'].message_type = _AD_UNIT
_AD_TEAM.fields_by_name['units'].message_type = _AD_UNIT
_AD_INIT.fields_by_name['team_entity'].message_type = _AD_TEAM
_AD_INIT.fields_by_name['puzzle_entity'].message_type = _AD_PUZZLE
_AD_ATTACK.fields_by_name['intensity'].enum_type = ad__enum__pb2._ENUM_ATTACK_INTENSITY
_AD_ATTACK.fields_by_name['color'].enum_type = ad__enum__pb2._ENUM_COLOR_TYPE
_AD_ATTACK.fields_by_name['damages'].message_type = _AD_DAMAGES
_AD_ENTITY_PANEL.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_AD_EFFECT.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_AD_EFFECT.fields_by_name['effect'].enum_type = ad__enum__pb2._ENUM_AD_EFFECT
_AD_EFFECT.fields_by_name['color'].enum_type = ad__enum__pb2._ENUM_COLOR_TYPE
DESCRIPTOR.message_types_by_name['ad_damages'] = _AD_DAMAGES
DESCRIPTOR.message_types_by_name['ad_unit'] = _AD_UNIT
DESCRIPTOR.message_types_by_name['ad_team'] = _AD_TEAM
DESCRIPTOR.message_types_by_name['ad_puzzle'] = _AD_PUZZLE
DESCRIPTOR.message_types_by_name['ad_init'] = _AD_INIT
DESCRIPTOR.message_types_by_name['ad_attack'] = _AD_ATTACK
DESCRIPTOR.message_types_by_name['ad_team_score_aciton'] = _AD_TEAM_SCORE_ACITON
DESCRIPTOR.message_types_by_name['ad_entity_panel'] = _AD_ENTITY_PANEL
DESCRIPTOR.message_types_by_name['ad_effect'] = _AD_EFFECT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ad_damages = _reflection.GeneratedProtocolMessageType('ad_damages', (_message.Message,), dict(
  DESCRIPTOR = _AD_DAMAGES,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_damages)
  ))
_sym_db.RegisterMessage(ad_damages)

ad_unit = _reflection.GeneratedProtocolMessageType('ad_unit', (_message.Message,), dict(
  DESCRIPTOR = _AD_UNIT,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_unit)
  ))
_sym_db.RegisterMessage(ad_unit)

ad_team = _reflection.GeneratedProtocolMessageType('ad_team', (_message.Message,), dict(
  DESCRIPTOR = _AD_TEAM,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_team)
  ))
_sym_db.RegisterMessage(ad_team)

ad_puzzle = _reflection.GeneratedProtocolMessageType('ad_puzzle', (_message.Message,), dict(
  DESCRIPTOR = _AD_PUZZLE,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_puzzle)
  ))
_sym_db.RegisterMessage(ad_puzzle)

ad_init = _reflection.GeneratedProtocolMessageType('ad_init', (_message.Message,), dict(
  DESCRIPTOR = _AD_INIT,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_init)
  ))
_sym_db.RegisterMessage(ad_init)

ad_attack = _reflection.GeneratedProtocolMessageType('ad_attack', (_message.Message,), dict(
  DESCRIPTOR = _AD_ATTACK,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_attack)
  ))
_sym_db.RegisterMessage(ad_attack)

ad_team_score_aciton = _reflection.GeneratedProtocolMessageType('ad_team_score_aciton', (_message.Message,), dict(
  DESCRIPTOR = _AD_TEAM_SCORE_ACITON,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_team_score_aciton)
  ))
_sym_db.RegisterMessage(ad_team_score_aciton)

ad_entity_panel = _reflection.GeneratedProtocolMessageType('ad_entity_panel', (_message.Message,), dict(
  DESCRIPTOR = _AD_ENTITY_PANEL,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_entity_panel)
  ))
_sym_db.RegisterMessage(ad_entity_panel)

ad_effect = _reflection.GeneratedProtocolMessageType('ad_effect', (_message.Message,), dict(
  DESCRIPTOR = _AD_EFFECT,
  __module__ = 'ad_behavior_pb2'
  # @@protoc_insertion_point(class_scope:ad_behavior.ad_effect)
  ))
_sym_db.RegisterMessage(ad_effect)


# @@protoc_insertion_point(module_scope)
