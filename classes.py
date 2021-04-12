# Class with all the info we need to know about each individual unit
class Unit:
    def __init__(self):
        self.apiId = 0
        self.createdTime = 0
        self.diedTime = 0
        self.survived = False
        self.name = 'marine'
        self.owner = '[Faze]xXx_l337_h4x0r_xXx'
        self.supply = 1

# A battle over a particular pot
class Battle:
    def __init__(self):
        self.units = []
        self.hands = []
        self.startTime = 0
        self.endTime = 0
        self.replay = '1.SC2Replay'
        # Conditions that determine whether the battle is useable, set by default to useable
        self.wildcard = False
        self.oneCard = False # If there are untyped units in the battle it will also be classified as a one card battle
        self.resolved = True # Did the battle finish before user quit?

# A card with a certain amount of one unit type
class Card:
    def __init__(self):
        self.unitType = 'marine'
        self.maxAmount = 50
        self.amount = 0
        self.owner = '[Faze]xXx_l337_h4x0r_xXx'
        self.lastDeathTime = 0

# A hand with two cards in it
class Hand:
    def __init__(self):
        self.card1 = None
        self.card2 = None
        self.won = False
        self.owner = '[Faze]xXx_l337_h4x0r_xXx'
        self.lastDeathTime = 0

# Class for analyzing the winrate of two hands against each other
class TwoHandMatchupAnalysis:
    def __init__(self):
        self.key = "Marine/Zergling vs Thor/Zealot"
        self.outcomes = [] # Array of numbers. 1 means left side won. 0 means right side won. 0.5 means draw.
        self.score = 0.5 # 0 means left side always loses, 1 means right side always wins, 0.5 means they usually tie.

# Class for analyzing the winrate of a hand against any hand
class TwoHandwinRateAnalysis:
    def __init__(self):
        self.key = "Marine/Zergling"
        self.outcomes = [] # Array of numbers. 1 means won. 0 means lose. 0.5 means draw.
        self.score = 0.5 # 0 means this hand always loses. 1 means this hand always wins, 0.5 means this hand always ties.

# Class for analyzing the winrate of one unit across all it's 2-card pairings
class UnitWinRateAnalysis:
    def __init__(self):
        self.key = "Marine"
        self.outcomes = [] # See above
        self.score = 0.5 # See above