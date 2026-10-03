"""
pairwise-football-manager-system - FootballManagerSystem

This module contains a deliberately broken implementation.
Fix all bugs so that tests pass.
"""


class FootballManagerSystem:
    def __init__(self):
        self.state = {}

    def update_player(self, *args, **kwargs):
        """BUG: 球员不做成长，训练了属性不变"""
        return None

    def apply_tactic(self, *args, **kwargs):
        """BUG: 战术不做阵型，433和442一样"""
        return None

    def transfer_player(self, *args, **kwargs):
        """BUG: 转会不做谈判，报价对方就接受"""
        return None

    def simulate_match(self, *args, **kwargs):
        """BUG: 比赛不做控球率，永远50:50"""
        return None

    def train_youth(self, *args, **kwargs):
        """BUG: 青训不做潜力，所有球员上限一样"""
        return None

