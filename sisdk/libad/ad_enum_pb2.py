# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ad_enum.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ad_enum.proto',
  package='ad_enum',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\rad_enum.proto\x12\x07\x61\x64_enum*u\n\x15\x65num_attack_intensity\x12\x0f\n\x0b\x61ttack_weak\x10\x00\x12\x13\n\x0f\x61ttack_moderate\x10\x01\x12\x10\n\x0c\x61ttack_heavy\x10\x02\x12\x11\n\rattack_charge\x10\x03\x12\x11\n\rattack_gather\x10\x04*F\n\x12\x65num_scenario_type\x12\x11\n\rall_scenarios\x10\x00\x12\x0e\n\nreal_scene\x10\x01\x12\r\n\tvir_scene\x10\x02*j\n\x0e\x65num_ad_effect\x12\x0b\n\x07\x64\x65\x66\x65nce\x10\x00\x12\x0b\n\x07\x65nhance\x10\x01\x12\x10\n\x0c\x63hange_color\x10\x02\x12\t\n\x05\x62link\x10\x03\x12\t\n\x05shake\x10\x04\x12\n\n\x06\x62ubble\x10\x05\x12\n\n\x06\x63harge\x10\x06*\xa9\x01\n\x10\x65num_device_type\x12\t\n\x05\x65mpty\x10\x00\x12\x0f\n\x0b\x63ore_router\x10\x01\x12\n\n\x06router\x10\x02\x12\n\n\x06switch\x10\x03\x12\x0c\n\x08\x66irewall\x10\x04\x12\x08\n\x04wlan\x10\x05\x12\x0b\n\x07storage\x10\x14\x12\x0b\n\x07printer\x10\x15\x12\n\n\x06server\x10\x32\x12\x0b\n\x07\x64\x65sktop\x10\x33\x12\n\n\x06laptop\x10\x34\x12\n\n\x06mobile\x10\x35*\x88\x01\n\x17\x65num_virtual_model_type\x12\n\n\x06\x65nmpty\x10\x00\x12\x15\n\x11vir_att_shipgroup\x10\x01\x12\x11\n\rvir_res_asset\x10\x02\x12\x16\n\x12vir_att_shipleader\x10\x03\x12\x0f\n\x0bvir_arbiter\x10\x04\x12\x0e\n\nvir_dazzle\x10\x05*\xbd\x01\n\x0f\x65num_panel_type\x12\x0e\n\nall_panels\x10\x00\x12\x14\n\x10scoreboard_panel\x10\x01\x12\x13\n\x0f\x65vent_log_panel\x10\x02\x12\x0f\n\x0bround_panel\x10\x03\x12\x14\n\x10match_name_panel\x10\x04\x12\x0f\n\x0btitle_panel\x10\x05\x12\x0e\n\nteam_panel\x10\x06\x12\x12\n\x0eprogress_panel\x10\x07\x12\x13\n\x0ftop_score_board\x10\x08*\xb2\x01\n\x0f\x65num_color_type\x12\x07\n\x03red\x10\x00\x12\n\n\x06yellow\x10\x01\x12\x08\n\x04\x62lue\x10\x03\x12\n\n\x06orange\x10\x04\x12\n\n\x06purple\x10\x05\x12\t\n\x05green\x10\x06\x12\x08\n\x04\x63yan\x10\x07\x12\x0b\n\x07magenta\x10\x08\x12\x08\n\x04red2\x10\t\x12\x0b\n\x07yellow2\x10\n\x12\t\n\x05\x62lue2\x10\x0b\x12\x0b\n\x07orange2\x10\x0c\x12\x0b\n\x07purple2\x10\r\x12\n\n\x06green2\x10\x0e\x62\x06proto3')
)

_ENUM_ATTACK_INTENSITY = _descriptor.EnumDescriptor(
  name='enum_attack_intensity',
  full_name='ad_enum.enum_attack_intensity',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='attack_weak', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='attack_moderate', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='attack_heavy', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='attack_charge', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='attack_gather', index=4, number=4,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=26,
  serialized_end=143,
)
_sym_db.RegisterEnumDescriptor(_ENUM_ATTACK_INTENSITY)

enum_attack_intensity = enum_type_wrapper.EnumTypeWrapper(_ENUM_ATTACK_INTENSITY)
_ENUM_SCENARIO_TYPE = _descriptor.EnumDescriptor(
  name='enum_scenario_type',
  full_name='ad_enum.enum_scenario_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='all_scenarios', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='real_scene', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_scene', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=145,
  serialized_end=215,
)
_sym_db.RegisterEnumDescriptor(_ENUM_SCENARIO_TYPE)

enum_scenario_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_SCENARIO_TYPE)
_ENUM_AD_EFFECT = _descriptor.EnumDescriptor(
  name='enum_ad_effect',
  full_name='ad_enum.enum_ad_effect',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='defence', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='enhance', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='change_color', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='blink', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='shake', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='bubble', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='charge', index=6, number=6,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=217,
  serialized_end=323,
)
_sym_db.RegisterEnumDescriptor(_ENUM_AD_EFFECT)

enum_ad_effect = enum_type_wrapper.EnumTypeWrapper(_ENUM_AD_EFFECT)
_ENUM_DEVICE_TYPE = _descriptor.EnumDescriptor(
  name='enum_device_type',
  full_name='ad_enum.enum_device_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='empty', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='core_router', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='router', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='switch', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='firewall', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='wlan', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='storage', index=6, number=20,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='printer', index=7, number=21,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='server', index=8, number=50,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='desktop', index=9, number=51,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='laptop', index=10, number=52,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='mobile', index=11, number=53,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=326,
  serialized_end=495,
)
_sym_db.RegisterEnumDescriptor(_ENUM_DEVICE_TYPE)

enum_device_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_DEVICE_TYPE)
_ENUM_VIRTUAL_MODEL_TYPE = _descriptor.EnumDescriptor(
  name='enum_virtual_model_type',
  full_name='ad_enum.enum_virtual_model_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='enmpty', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_att_shipgroup', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_res_asset', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_att_shipleader', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_arbiter', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vir_dazzle', index=5, number=5,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=498,
  serialized_end=634,
)
_sym_db.RegisterEnumDescriptor(_ENUM_VIRTUAL_MODEL_TYPE)

enum_virtual_model_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_VIRTUAL_MODEL_TYPE)
_ENUM_PANEL_TYPE = _descriptor.EnumDescriptor(
  name='enum_panel_type',
  full_name='ad_enum.enum_panel_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='all_panels', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='scoreboard_panel', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='event_log_panel', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='round_panel', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='match_name_panel', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='title_panel', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='team_panel', index=6, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='progress_panel', index=7, number=7,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='top_score_board', index=8, number=8,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=637,
  serialized_end=826,
)
_sym_db.RegisterEnumDescriptor(_ENUM_PANEL_TYPE)

enum_panel_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_PANEL_TYPE)
_ENUM_COLOR_TYPE = _descriptor.EnumDescriptor(
  name='enum_color_type',
  full_name='ad_enum.enum_color_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='red', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='yellow', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='blue', index=2, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='orange', index=3, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='purple', index=4, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='green', index=5, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='cyan', index=6, number=7,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='magenta', index=7, number=8,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='red2', index=8, number=9,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='yellow2', index=9, number=10,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='blue2', index=10, number=11,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='orange2', index=11, number=12,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='purple2', index=12, number=13,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='green2', index=13, number=14,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=829,
  serialized_end=1007,
)
_sym_db.RegisterEnumDescriptor(_ENUM_COLOR_TYPE)

enum_color_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_COLOR_TYPE)
attack_weak = 0
attack_moderate = 1
attack_heavy = 2
attack_charge = 3
attack_gather = 4
all_scenarios = 0
real_scene = 1
vir_scene = 2
defence = 0
enhance = 1
change_color = 2
blink = 3
shake = 4
bubble = 5
charge = 6
empty = 0
core_router = 1
router = 2
switch = 3
firewall = 4
wlan = 5
storage = 20
printer = 21
server = 50
desktop = 51
laptop = 52
mobile = 53
enmpty = 0
vir_att_shipgroup = 1
vir_res_asset = 2
vir_att_shipleader = 3
vir_arbiter = 4
vir_dazzle = 5
all_panels = 0
scoreboard_panel = 1
event_log_panel = 2
round_panel = 3
match_name_panel = 4
title_panel = 5
team_panel = 6
progress_panel = 7
top_score_board = 8
red = 0
yellow = 1
blue = 3
orange = 4
purple = 5
green = 6
cyan = 7
magenta = 8
red2 = 9
yellow2 = 10
blue2 = 11
orange2 = 12
purple2 = 13
green2 = 14


DESCRIPTOR.enum_types_by_name['enum_attack_intensity'] = _ENUM_ATTACK_INTENSITY
DESCRIPTOR.enum_types_by_name['enum_scenario_type'] = _ENUM_SCENARIO_TYPE
DESCRIPTOR.enum_types_by_name['enum_ad_effect'] = _ENUM_AD_EFFECT
DESCRIPTOR.enum_types_by_name['enum_device_type'] = _ENUM_DEVICE_TYPE
DESCRIPTOR.enum_types_by_name['enum_virtual_model_type'] = _ENUM_VIRTUAL_MODEL_TYPE
DESCRIPTOR.enum_types_by_name['enum_panel_type'] = _ENUM_PANEL_TYPE
DESCRIPTOR.enum_types_by_name['enum_color_type'] = _ENUM_COLOR_TYPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)
