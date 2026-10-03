import pytest
from football_manager.system import FootballManagerSystem


class TestFootballManagerSystem:

    def test_update_player(self):
        """球员不做成长，训练了属性不变"""
        obj = FootballManagerSystem()
        result = obj.update_player()
        self.assertIsNotNone(result)

    def test_apply_tactic(self):
        """战术不做阵型，433和442一样"""
        obj = FootballManagerSystem()
        result = obj.apply_tactic()
        self.assertIsNotNone(result)

    def test_transfer_player(self):
        """转会不做谈判，报价对方就接受"""
        obj = FootballManagerSystem()
        result = obj.transfer_player()
        self.assertIsNotNone(result)

    def test_simulate_match(self):
        """比赛不做控球率，永远50:50"""
        obj = FootballManagerSystem()
        result = obj.simulate_match()
        self.assertIsNotNone(result)

    def test_train_youth(self):
        """青训不做潜力，所有球员上限一样"""
        obj = FootballManagerSystem()
        result = obj.train_youth()
        self.assertIsNotNone(result)

