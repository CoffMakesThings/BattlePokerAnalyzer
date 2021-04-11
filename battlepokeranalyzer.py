import sys
import sc2reader
import json
import os
from pprint import pprint

# Class with all the info we need to know about units
class Unit:
    def __init__(self):
        self.apiId = 0
        self.createdTime = 0
        self.diedTime = 0
        self.survived = False
        self.name = 'marine'
        self.owner = '[Faze]xXx_l337_h4x0r_xXx'

# A battle over a particular pot
class Battle:
    def __init__(self):
        self.units = []
        self.cards = []
        self.hands = []
        self.startTime = 0
        self.endTime = 0
        self.hasWildcard = False

# A card with a certain amount of one unit type
class Card:
    def __init__(self):
        self.unitType = 'marine'
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

# Class for analyzing many hands that have the same cards
class HandAnalysis:
    def __init__(self):
        self.key = "Marine/Zergling vs Thor/Zealot"
        self.outcomes = [] # Array of numbers. 1 means left side won. 0 means right side won. 0.5 means draw.
        self.score = 0.5 # 0 means left side always loses, 1 means right side always wins, 0.5 means they usually tie

# Interesting helpful facts
# 84 is the y coordinate of the bottom-most player, helpful for filtering out avatar units

# List of units to ignore like broodlings and locusts
ignoredUnits = [
    'BroodlingEscort',
    'Broodling',
    'Locust',
    'InfestedTerransEgg',
    'InfestedTerran',
    'Interceptor',
##    'SiegeTankSieged',
##    'LurkerBurrowed',
##    'WidowMineBurrowed',
##    'LiberatorAG'
]

replaysPath = 'replays2/'

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
                unit.owner = apiUnit['owner']
                units.append(unit)

    # Derive battles from units
    battles = []
    print("Iterating units")

    for unit in units:
        if any(battle.startTime == unit.createdTime for battle in battles):
            battle = next(battle for battle in battles if battle.startTime == unit.createdTime)
            battle.units.append(unit)
##            print(vars(unit))
            if battle.endTime < unit.diedTime:
                battle.endTime = unit.diedTime
        else:
            battle = Battle()
            battle.units.append(unit)
            battle.startTime = unit.createdTime
            battle.endTime = unit.diedTime
            battles.append(battle)

    # Derive cards and hands from battles
    print("Iterating battles")

    for battle in battles:
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

battles = []

# Iterate through replays to collect all the battles
maxFilesToAnalyze = 10
counter = 0
print("Iterating replays")

for file in os.listdir(replaysPath):
    if counter < maxFilesToAnalyze:
        battles += analyzeFile(replaysPath + file)
        counter += 1
        print(str(counter) + "/" + str(len(os.listdir(replaysPath))) + " replays processed")

# Dictionary of outcomes by 2 hand battles
twoHandDict = {}

twoHandBattles = [battle for battle in battles if len(battle.hands) == 2]

print("Iterating two hand battles")

for battle in twoHandBattles:
    key = battle.hands[0].card1.unitType + "/" + battle.hands[0].card2.unitType + " vs " + battle.hands[1].card1.unitType + "/" + battle.hands[1].card2.unitType
    if key not in twoHandDict:
        handAnalysis = HandAnalysis()
        handAnalysis.key = key
        twoHandDict[key] = handAnalysis
    if (battle.hands[0].won and battle.hands[1].won):
        twoHandDict[key].outcomes.append(0.5)
    elif (battle.hands[0].won):
        twoHandDict[key].outcomes.append(1)
    else:
        twoHandDict[key].outcomes.append(0)

# Derive a score based on outcomes
for key in twoHandDict:
    twoHandDict[key].score = sum(twoHandDict[key].outcomes) / len(twoHandDict[key].outcomes)

# Some stats
totalCards = 0
totalHands = 0

for battle in battles:
    totalCards += len(battle.cards)
    totalHands += len(battle.hands)

# Save to file
with open("events.log", "w") as log_file:
    sys.stdout = log_file
    print(str(len(battles)) + " battles")
    print(str(len([battle for battle in battles if battle.hasWildcard])) + " battles with wildcards (ignored)")
    print(str(len(twoHandBattles)) + " two hand battles")
    print(str(len([battle for battle in twoHandBattles if battle.hasWildcard])) + " two hand battles with wildcards (ignored)")
    print(str(totalHands) + " hands")
    print(str(totalCards) + " cards")
    print("\nHandAnalyses\n")
    dictKeys = twoHandDict.keys()
    dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandDict[dictKey].score)
    for key in dictKeys:
        print(key)
        print(twoHandDict[key].score)
##    print("\nBattles\n")
##    for battle in battles:
##        pprint(vars(battle))
##    print("\nUnits\n")
##    for unit in units:
##        pprint(vars(unit))
