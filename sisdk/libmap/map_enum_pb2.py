# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: map_enum.proto

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
  name='map_enum.proto',
  package='map_enum',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0emap_enum.proto\x12\x08map_enum*4\n\x11\x65num_attack_speed\x12\x08\n\x04slow\x10\x00\x12\x0b\n\x07middile\x10\x01\x12\x08\n\x04\x66\x61st\x10\x02*\x80\x01\n\x0b\x65num_effect\x12\x0b\n\x07\x64\x65\x66\x65nce\x10\x00\x12\x0b\n\x07\x65nhance\x10\x01\x12\x10\n\x0c\x63hange_color\x10\x02\x12\t\n\x05smoke\x10\x03\x12\x0b\n\x07war_fog\x10\x04\x12\x0e\n\nradar_anim\x10\x05\x12\x08\n\x04icon\x10\x06\x12\x13\n\x0fnamepanel_color\x10\x07*d\n\x10\x65num_effect_icon\x12\x0b\n\x07no_icon\x10\x00\x12\x0f\n\x0b\x65xclamation\x10\x01\x12\x0f\n\x0binformation\x10\x02\x12\x0c\n\x08question\x10\x03\x12\n\n\x06wrench\x10\x04\x12\x07\n\x03\x63og\x10\x05*\'\n\x0b\x65num_status\x12\n\n\x06normal\x10\x00\x12\x0c\n\x08\x64owntime\x10\x01*\xe6\x01\n\x0f\x65num_model_type\x12\x0c\n\x08warplane\x10\x00\x12\t\n\x05\x64rone\x10\x01\x12\r\n\tsatellite\x10\x02\x12\t\n\x05radar\x10\x03\x12\r\n\tsubmarine\x10\x04\x12\r\n\tdestroyer\x10\x05\x12\x14\n\x10\x61ircraft_carrier\x10\x06\x12\x12\n\x0e\x63ommand_center\x10\x07\x12\x10\n\x0c\x63ommand_post\x10\x08\x12\x18\n\x14\x63ommunications_tower\x10\t\x12\x08\n\x04reef\x10\n\x12\x11\n\rpower_station\x10\x0b\x12\x0f\n\x0bplaceholder\x10\x0c*\xac\x01\n\x0f\x65num_panel_type\x12\x0e\n\nall_panels\x10\x00\x12\x14\n\x10scoreboard_panel\x10\x01\x12\x13\n\x0f\x65vent_log_panel\x10\x02\x12\x0f\n\x0bround_panel\x10\x03\x12\x14\n\x10match_name_panel\x10\x04\x12\x0e\n\nteam_panel\x10\x05\x12\x12\n\x0eprogress_panel\x10\x07\x12\x13\n\x0ftop_score_board\x10\x08\x62\x06proto3')
)

_ENUM_ATTACK_SPEED = _descriptor.EnumDescriptor(
  name='enum_attack_speed',
  full_name='map_enum.enum_attack_speed',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='slow', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='middile', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='fast', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=28,
  serialized_end=80,
)
_sym_db.RegisterEnumDescriptor(_ENUM_ATTACK_SPEED)

enum_attack_speed = enum_type_wrapper.EnumTypeWrapper(_ENUM_ATTACK_SPEED)
_ENUM_EFFECT = _descriptor.EnumDescriptor(
  name='enum_effect',
  full_name='map_enum.enum_effect',
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
      name='smoke', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='war_fog', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='radar_anim', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='icon', index=6, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='namepanel_color', index=7, number=7,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=83,
  serialized_end=211,
)
_sym_db.RegisterEnumDescriptor(_ENUM_EFFECT)

enum_effect = enum_type_wrapper.EnumTypeWrapper(_ENUM_EFFECT)
_ENUM_EFFECT_ICON = _descriptor.EnumDescriptor(
  name='enum_effect_icon',
  full_name='map_enum.enum_effect_icon',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='no_icon', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='exclamation', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='information', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='question', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='wrench', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='cog', index=5, number=5,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=213,
  serialized_end=313,
)
_sym_db.RegisterEnumDescriptor(_ENUM_EFFECT_ICON)

enum_effect_icon = enum_type_wrapper.EnumTypeWrapper(_ENUM_EFFECT_ICON)
_ENUM_STATUS = _descriptor.EnumDescriptor(
  name='enum_status',
  full_name='map_enum.enum_status',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='normal', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='downtime', index=1, number=1,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=315,
  serialized_end=354,
)
_sym_db.RegisterEnumDescriptor(_ENUM_STATUS)

enum_status = enum_type_wrapper.EnumTypeWrapper(_ENUM_STATUS)
_ENUM_MODEL_TYPE = _descriptor.EnumDescriptor(
  name='enum_model_type',
  full_name='map_enum.enum_model_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='warplane', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='drone', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='satellite', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='radar', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='submarine', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='destroyer', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='aircraft_carrier', index=6, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='command_center', index=7, number=7,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='command_post', index=8, number=8,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='communications_tower', index=9, number=9,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='reef', index=10, number=10,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='power_station', index=11, number=11,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='placeholder', index=12, number=12,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=357,
  serialized_end=587,
)
_sym_db.RegisterEnumDescriptor(_ENUM_MODEL_TYPE)

enum_model_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_MODEL_TYPE)
_ENUM_PANEL_TYPE = _descriptor.EnumDescriptor(
  name='enum_panel_type',
  full_name='map_enum.enum_panel_type',
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
      name='team_panel', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='progress_panel', index=6, number=7,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='top_score_board', index=7, number=8,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=590,
  serialized_end=762,
)
_sym_db.RegisterEnumDescriptor(_ENUM_PANEL_TYPE)

enum_panel_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_PANEL_TYPE)
slow = 0
middile = 1
fast = 2
defence = 0
enhance = 1
change_color = 2
smoke = 3
war_fog = 4
radar_anim = 5
icon = 6
namepanel_color = 7
no_icon = 0
exclamation = 1
information = 2
question = 3
wrench = 4
cog = 5
normal = 0
downtime = 1
warplane = 0
drone = 1
satellite = 2
radar = 3
submarine = 4
destroyer = 5
aircraft_carrier = 6
command_center = 7
command_post = 8
communications_tower = 9
reef = 10
power_station = 11
placeholder = 12
all_panels = 0
scoreboard_panel = 1
event_log_panel = 2
round_panel = 3
match_name_panel = 4
team_panel = 5
progress_panel = 7
top_score_board = 8


DESCRIPTOR.enum_types_by_name['enum_attack_speed'] = _ENUM_ATTACK_SPEED
DESCRIPTOR.enum_types_by_name['enum_effect'] = _ENUM_EFFECT
DESCRIPTOR.enum_types_by_name['enum_effect_icon'] = _ENUM_EFFECT_ICON
DESCRIPTOR.enum_types_by_name['enum_status'] = _ENUM_STATUS
DESCRIPTOR.enum_types_by_name['enum_model_type'] = _ENUM_MODEL_TYPE
DESCRIPTOR.enum_types_by_name['enum_panel_type'] = _ENUM_PANEL_TYPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)
