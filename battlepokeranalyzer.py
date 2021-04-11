import sys
import sc2reader
import json
import os
from pprint import pprint

# ----------------------------------- CONFIGURATION ------------------------------------------ #

# Max amount of supply that a card can have
maxSupply = 50

# List of units to ignore like broodlings and locusts
ignoredUnits = [
    'BroodlingEscort',
    'Broodling',
    'Locust',
    'InfestedTerransEgg',
    'InfestedTerran',
    'Interceptor',
##    For some reason I don't think these need to be excluded, keeping them here in case
##    'SiegeTankSieged',
##    'LurkerBurrowed',
##    'WidowMineBurrowed',
##    'LiberatorAG'
]

# Analyze this many replays maximum, make small for quick tests
maxFilesToAnalyze = 100

# Analyze replays in this relative directory
replaysPath = 'replays/'

# Interesting helpful facts
# 84 is the y coordinate of the bottom-most player, helpful for filtering out avatar units

# -------------------------------------------------------------------------------------------- #

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
        self.cards = []
        self.hands = []
        self.startTime = 0
        self.endTime = 0
        self.hasWildcard = False
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

# Analyze one file and add the results to battles
def analyzeFile(filePath):
    print("Processing replay at " + filePath)
    
    # Get all the unit birth/death events from sc2reader
    replay = sc2reader.load_replay(filePath, load_level=4)
    trackerEvents = vars(replay)['raw_data']['replay.tracker.events'];
    birthAndDeathEvents = [event for event in trackerEvents
                           if vars(event)['name'] == 'UnitDiedEvent' or vars(event)['name'] == 'UnitBornEvent']

    # Derive units from birth and death events
    units = []
    print("Iterating events")

    for birthAndDeathEvent in birthAndDeathEvents:
        apiUnit = vars(vars(birthAndDeathEvent)['unit'])
        # Ignore avatar units and unit types from ignored lists
        if apiUnit['location'][1] < 84 and not any(ignoredUnit == vars(apiUnit['_type_class'])['name'] for ignoredUnit in ignoredUnits):
            # Use unit id to check if this unit is already in our list
            if not any(unit.apiId == apiUnit['id'] for unit in units):
                # It's not added yet, add to list
                unit = Unit()
                apiUnit = vars(vars(birthAndDeathEvent)['unit'])
                unit.apiId = apiUnit['id']
                unit.createdTime = apiUnit['started_at']
                unit.diedTime = apiUnit['died_at']
                unit.survived = apiUnit['killing_unit'] is None
                unit.name = vars(apiUnit['_type_class'])['name']
                unit.supply = vars(apiUnit['_type_class'])['supply']
                unit.owner = apiUnit['owner']
                units.append(unit)

    # Derive battles from units
    battles = []
    print("Iterating units")

    for unit in units:
        if any(battle.startTime == unit.createdTime for battle in battles):
            battle = next(battle for battle in battles if battle.startTime == unit.createdTime)
            battle.units.append(unit)
            if unit.diedTime is None:
                battle.resolved = False
            elif battle.endTime < unit.diedTime:
                battle.endTime = unit.diedTime
        else:
            battle = Battle()
            battle.units.append(unit)
            battle.startTime = unit.createdTime
            if unit.diedTime is None:
                battle.resolved = False
            else:
                battle.endTime = unit.diedTime
            battles.append(battle)

    # Derive cards and hands from battles
    print("Iterating battles")

    for battle in battles:
        if battle.resolved:
            # Detect battles with wildcards - Won't deal with wildcards for now
            unitTypes = {unit.name for unit in battle.units}
            owners = {unit.owner for unit in battle.units}
            # print("Battle starting at " + str(battle.startTime))

            if len(unitTypes) > 2 * len(owners):
                # Wildcard battle, fuck all that
                battle.hasWildcard = True
            else:
                # Not a wildcard battle, let's derive cards
                for unitType in unitTypes:
                    card = Card()
                    card.unitType = unitType
                    cardUnits = [unit for unit in battle.units if unit.name == unitType]
                    card.amount = len(cardUnits)
                    card.owner = cardUnits[0].owner
                    card.maxAmount = maxSupply / cardUnits[0].supply
                    card.lastDeathTime = max(unit.diedTime for unit in cardUnits)
                    battle.cards.append(card)

                # Now lets derive hands
                battle.cards = sorted(battle.cards, key=lambda card: card.unitType)
                for card in battle.cards:
                    if any(card.owner == hand.owner for hand in battle.hands):
                        hand = next(hand for hand in battle.hands if hand.owner == card.owner)
                        hand.card2 = card
                        hand.lastDeathTime = max([hand.card1.lastDeathTime, hand.card2.lastDeathTime])
                        if hand.lastDeathTime == battle.endTime:
                            hand.won = True
                    else:
                        hand = Hand()
                        hand.owner = card.owner
                        hand.card1 = card
                        battle.hands.append(hand)

    return battles

# Generate dictionary of outcomes by 2 hand battles
def generateTwoHandMatchupAnalysis(battles):
    twoHandMatchupDict = {}

    twoHandBattles = getUseableTwoHandBattles()

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        key = battle.hands[0].card1.unitType + "/" + battle.hands[0].card2.unitType + " vs " + battle.hands[1].card1.unitType + "/" + battle.hands[1].card2.unitType
        if key not in twoHandMatchupDict:
            handAnalysis = TwoHandMatchupAnalysis()
            handAnalysis.key = key
            twoHandMatchupDict[key] = handAnalysis
        if (battle.hands[0].won and battle.hands[1].won):
            twoHandMatchupDict[key].outcomes.append(0.5)
        elif (battle.hands[0].won):
            twoHandMatchupDict[key].outcomes.append(1)
        else:
            twoHandMatchupDict[key].outcomes.append(0)

    # Derive a score based on outcomes
    for key in twoHandMatchupDict:
        twoHandMatchupDict[key].score = sum(twoHandMatchupDict[key].outcomes) / len(twoHandMatchupDict[key].outcomes)

    return twoHandMatchupDict

# Generate dictionary of outcomes by 2 hand battles
def generateTwoHandwinRatesByHandAnalysis(battles):
    twoHandWinRateDict = {}

    twoHandBattles = getUseableTwoHandBattles()

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        key = battle.hands[0].card1.unitType + "/" + battle.hands[0].card2.unitType
        if key not in twoHandWinRateDict:
            handAnalysis = TwoHandwinRateAnalysis()
            handAnalysis.key = key
            twoHandWinRateDict[key] = handAnalysis
        if (battle.hands[0].won and battle.hands[1].won):
            twoHandWinRateDict[key].outcomes.append(0.5)
        elif (battle.hands[0].won):
            twoHandWinRateDict[key].outcomes.append(1)
        else:
            twoHandWinRateDict[key].outcomes.append(0)
        key = battle.hands[1].card1.unitType + "/" + battle.hands[1].card2.unitType
        if key not in twoHandWinRateDict:
            handAnalysis = TwoHandwinRateAnalysis()
            handAnalysis.key = key
            twoHandWinRateDict[key] = handAnalysis
        if (battle.hands[0].won and battle.hands[1].won):
            twoHandWinRateDict[key].outcomes.append(0.5)
        elif (battle.hands[0].won):
            twoHandWinRateDict[key].outcomes.append(1)
        else:
            twoHandWinRateDict[key].outcomes.append(0)

    # Derive a score based on outcomes
    for key in twoHandWinRateDict:
        twoHandWinRateDict[key].score = sum(twoHandWinRateDict[key].outcomes) / len(twoHandWinRateDict[key].outcomes)

    return twoHandWinRateDict

def getUseableTwoHandBattles():
    return [battle for battle in battles if len(battle.hands) == 2 and battle.resolved]

battles = []

# Iterate through replays to collect all the battles
counter = 0
print("Iterating replays")

for file in os.listdir(replaysPath):
    if counter < maxFilesToAnalyze:
        battles += analyzeFile(replaysPath + file)
        counter += 1
        print(str(counter) + "/" + str(len(os.listdir(replaysPath))) + " replays processed")

# Generate dictionary of scores of particular hand matchups
twoHandMatchupDict = generateTwoHandMatchupAnalysis(battles)

# Generate dictionary of scores of hands in any 2 hand battle
twoHandWinRateDict = generateTwoHandwinRatesByHandAnalysis(battles)

# Save current stdout
originalStdOut = sys.stdout

# Produce log file
with open("output.log", "w") as log_file:
    # Log stats about how much data was used
    sys.stdout = log_file
    print(str(len(battles)) + " total battles found")
    print(str(len([battle for battle in battles if battle.hasWildcard])) + " battles with wildcards were excluded")
    print(str(len([battle for battle in battles if not battle.resolved])) + " unresolved battles were excluded")
    print(str(len(getUseableTwoHandBattles())) + " useable two hand battles remained")

    # Write two hand win rate analyses to log
    print("\nHand win rate in two-hand battles\n")

    dictKeys = twoHandWinRateDict.keys()
    dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandWinRateDict[dictKey].score)
    for key in dictKeys:
        print(key)
        print(str(len(twoHandWinRateDict[key].outcomes)) + " battles found")
        print(twoHandWinRateDict[key].score)

    # Write two hand matchup analyses to log
    print("\nHand win rates vs other particular hands in two-hand battles\n")

    dictKeys = twoHandMatchupDict.keys()
    dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandMatchupDict[dictKey].score)
    for key in dictKeys:
        print(key)
        print(str(len(twoHandMatchupDict[key].outcomes)) + " battles found")
        print(twoHandMatchupDict[key].score)

# Produce csv files
with open("TwoHandWinRatesByHand.csv", "w") as csv_file:
    sys.stdout = csv_file

    # Write two hand win rate analyses to csv
    dictKeys = twoHandWinRateDict.keys()
    dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandWinRateDict[dictKey].score)
    print('Hand,Battles,Winrate')
    for key in dictKeys:
        print('{},{},{}'.format(key, len(twoHandWinRateDict[key].outcomes), twoHandWinRateDict[key].score))

with open("TwoHandMatchups.csv", "w") as csv_file:
    sys.stdout = csv_file

    # Write two hand matchup analyses to csv
    dictKeys = twoHandMatchupDict.keys()
    dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandMatchupDict[dictKey].score)
    print('Matchup,Battles,Winrate')
    for key in dictKeys:
        print('{},{},{}'.format(key, len(twoHandMatchupDict[key].outcomes), twoHandMatchupDict[key].score))

sys.stdout = originalStdOut
print("Process complete, find results in output.log, TwoHandWinRatesByHand.csv and TwoHandMatchups.csv")
