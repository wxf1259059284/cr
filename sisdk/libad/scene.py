#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-9 上午9:08
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : scene.py.py
# @Project : cpss

import sisdk.libad.enums as ad_enums
from .ad_behavior_pb2 import ad_team, ad_unit, ad_puzzle, ad_init
from sisdk.messages import wrap_message

class AdScene(object):
    def __init__(self):
        self.tasks = []
        self.puzzles = []
        self.teams = []

    def add_task(self, task_id, task_name):
        task = {"id": task_id, "name": task_name}
        task_exists = False
        for t in self.tasks:
            if t["id"] == task_id:
                t.update(task)
                task_exists = True
        if not task_exists:
            self.tasks.append(task)

    def add_team(self, team_id, team_name, team_logo='', init_score=0, team_color=''):
        team = {"id": team_id,
                "name": team_name,
                "logo": team_logo,
                "score": init_score,
                "color": team_color}
        team_exists = False
        for t in self.teams:
            if t["id"] == team_id:
                t.update(team)
                team_exists = True
        if not team_exists:
            self.teams.append(team)

    def add_puzzle(self, puzzle_id, puzzle_name, puzzle_score, puzzle_solved):
        puzzle = {"id": puzzle_id,
                  "name": puzzle_name,
                  "title_score": puzzle_score,
                  "solved": puzzle_solved
                  }
        puzzle_exists = False
        for t in self.puzzles:
            if t["id"] == puzzle_id:
                t.update(puzzle)
                puzzle_exists = True
        if not puzzle_exists:
            self.puzzles.append(puzzle)

    def get_task_binary(self, team_id, color):
        # task对应的proto是unit
        units_bin = []
        for ts in self.tasks:
            ts_unit = ad_unit(id="unit-%s-%s" % (str(team_id), str(ts['id'])),
                              device_type=ad_enums.EnumDeviceType.server,
                              model_type=ad_enums.EnumVirtualModelType.vir_res_asset,
                              color=color,
                              show_children=True)
            units_bin.append(ts_unit)
        dummy_unit = ad_unit(id="dummy-%s" % str(team_id),
                             device_type=ad_enums.EnumDeviceType.firewall,
                             model_type=ad_enums.EnumVirtualModelType.vir_att_shipgroup,
                             color=color,
                             show_children=True)
        dummy_unit.units.extend(units_bin)
        return dummy_unit

    def get_team_binary(self):
        teams_bin = []
        for tm in self.teams:
            units = self.get_task_binary(tm['id'], tm['color'])
            tm_bin = ad_team(**tm)
            tm_bin.units.extend([units])
            teams_bin.append(tm_bin)
        return teams_bin

    def get_puzzle_binary(self):
        puzzles_bin = []
        for p in self.puzzles:
            p_bin = ad_puzzle(**p)
            puzzles_bin.append(p_bin)
        return puzzles_bin

    def to_binary(self):
        b_teams = self.get_team_binary()
        b_puzzles = self.get_puzzle_binary()
        b_init = ad_init(team_entity=b_teams, puzzle_entity=b_puzzles)
        return wrap_message(b_init)

    def to_json(self):
        pass