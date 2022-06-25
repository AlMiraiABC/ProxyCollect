from unittest import TestCase
from util.config import ScoreConfig

from util.score import Score


class TestScore(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ScoreConfig.CEILING = 50
        ScoreConfig.NADIR = -20
        ScoreConfig.INIT = 20
        ScoreConfig.INCREASE = 1
        ScoreConfig.DECREASE = 1

    def test_score_inc(self):
        S = 30
        v = Score.calc(0.58, S)
        self.assertEqual(v, S+ScoreConfig.INCREASE)

    def test_score_inc_max(self):
        S = ScoreConfig.CEILING
        v = Score.calc(0.58, S)
        self.assertEqual(v, ScoreConfig.CEILING)

    def test_score_inc_init(self):
        S = 10
        v = Score.calc(0.58, S)
        self.assertEqual(v, ScoreConfig.INIT)

    def test_score_dec(self):
        S = 30
        R = -1
        v = Score.calc(R, S)
        self.assertEqual(v, S+R*ScoreConfig.DECREASE)

    def test_score_dec_2(self):
        S = 30
        R = -2
        v = Score.calc(R, S)
        self.assertEqual(v, S+R*ScoreConfig.DECREASE)

    def test_score_dec_min(self):
        S = -20
        R = -1
        v = Score.calc(R, S)
        self.assertEqual(v, ScoreConfig.NADIR)

    def test_score_dec_min_2(self):
        S = ScoreConfig.NADIR-1
        R = -2
        v = Score.calc(R, S)
        self.assertEqual(v, ScoreConfig.NADIR)
