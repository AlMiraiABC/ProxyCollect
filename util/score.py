from util.config import ScoreConfig


class Score:
    @staticmethod
    def calc(speed: float, score: int) -> int:
        """
        Calculate score.

        :param speed: Seconds. >0 if available. <0 if error, decrease rate.
        :param score: Current score before update.
        :return: Calc result. The new score.

        Examples:
        -------------------
        >>> CEILING, NADIR, INIT = 50, -20, 20
        >>> INCREASE, DECREASE = 1, 1
        >>> # available
        >>> Score.calc(0.58, 30)
            31
        >>> Score.calc(0.58, 50) # maximum
            50
        >>> Score.calc(0.58, 10) # Available again. Set to init.
            20
        >>> # unavailable
        >>> Score.calc(-1, 30)
            29
        >>> Score.calc(-2, 30)
            28
        >>> Score.calc(-1, -20) # minimum
            -20
        >>> Score.calc(-2, -49) # minimum
            -20
        """
        if speed < 0:  # timeout or raise err
            if score+speed <= ScoreConfig.NADIR:
                return ScoreConfig.NADIR
            return score+speed*ScoreConfig.DECREASE # decrease rate
        if speed >= 0:
            if score+speed >= ScoreConfig.CEILING: # max
                return ScoreConfig.CEILING
            if score < ScoreConfig.INIT:  # set to init if it's unavailable.
                return ScoreConfig.INIT
            return score+ScoreConfig.INCREASE
