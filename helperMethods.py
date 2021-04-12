import os
import configuration
import shutil
import sc2reader
import classes

# Move all replays from the replays folders into the processing folder, renamed such that they dont overwrite each other
def prepareProcessingDirectory():
    print("Preparing processing folder")
    counter = 0

    # Delete processing folder
    if os.path.exists(configuration.processingPath):
        shutil.rmtree(configuration.processingPath)

    # Make processing folder
    os.mkdir(configuration.processingPath)

    # Move replays in
    for directory in configuration.replayDirectories:
        for file in os.listdir(directory):
            print("Moving {} to {}".format('{}{}'.format(directory, file), '{}{}.SC2Replay'.format(configuration.processingPath, counter)))
            shutil.copyfile('{}{}'.format(directory, file), '{}{}.SC2Replay'.format(configuration.processingPath, counter))
            counter += 1


# Analyze one file and derive battles based on when units were created and died
def analyzeFile(filePath):
    print("Processing replay at " + filePath)
    
    # Get all the unit birth/death events from sc2reader
    replay = sc2reader.load_replay(filePath, load_level=4)
    trackerEvents = vars(replay)['raw_data']['replay.tracker.events'];
    birthAndDeathEvents = [event for event in trackerEvents
                           if vars(event)['name'] == 'UnitDiedEvent' or vars(event)['name'] == 'UnitBornEvent']

    # Derive units from birth and death events
    units = []
    print("Deriving units from replay events")

    for birthAndDeathEvent in birthAndDeathEvents:
        apiUnit = vars(vars(birthAndDeathEvent)['unit'])
        # Ignore avatar units and unit types from ignored lists
        if apiUnit['location'][1] < configuration.lowestAvatarUnitYCoordinate and not any(ignoredUnit == vars(apiUnit['_type_class'])['name'] for ignoredUnit in configuration.ignoredUnits):
            # Use unit id to check if this unit is already in our list
            if not any(unit.apiId == apiUnit['id'] for unit in units):
                # It's not added yet, add to list
                unit = classes.Unit()
                apiUnit = vars(vars(birthAndDeathEvent)['unit'])
                unit.apiId = apiUnit['id']
                unit.createdTime = apiUnit['started_at']
                unit.diedTime = apiUnit['died_at']
                unit.survived = apiUnit['killing_unit'] is None
                unit.name = vars(apiUnit['_type_class'])['name']
                unit.supply = vars(apiUnit['_type_class'])['supply']
                if (unit.supply == 0):
                    unit.supply = 1 # Dirty temporary hack to avoid divide by 0 error, some units have 0 sup
                unit.owner = apiUnit['owner']
                units.append(unit)

    # Derive battles from units
    battles = []
    print("Deriving battles from units")

    for unit in units:
        if any(battle.startTime == unit.createdTime for battle in battles):
            battle = next(battle for battle in battles if battle.startTime == unit.createdTime)
            battle.units.append(unit)
            if unit.diedTime is None:
                battle.resolved = False
            elif battle.endTime < unit.diedTime:
                battle.endTime = unit.diedTime
        else:
            battle = classes.Battle()
            battle.units.append(unit)
            battle.startTime = unit.createdTime
            if unit.diedTime is None:
                battle.resolved = False
            else:
                battle.endTime = unit.diedTime
            battles.append(battle)

    # Derive cards and hands from battles
    print("Deriving cards and hands from battles")

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
                    card = classes.Card()
                    card.unitType = unitType
                    cardUnits = [unit for unit in battle.units if unit.name == unitType]
                    card.amount = len(cardUnits)
                    card.owner = cardUnits[0].owner
                    card.maxAmount = configuration.maxSupply / cardUnits[0].supply
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
                        hand = classes.Hand()
                        hand.owner = card.owner
                        hand.card1 = card
                        battle.hands.append(hand)

    return battles

# Generate dictionary of outcomes by 2 hand battles
def generateTwoHandMatchupAnalysis(battles):
    print("Generating two hand matchup analysis")

    twoHandMatchupDict = {}

    twoHandBattles = getUseableTwoHandBattles(battles)

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        key = battle.hands[0].card1.unitType + "/" + battle.hands[0].card2.unitType + " vs " + battle.hands[1].card1.unitType + "/" + battle.hands[1].card2.unitType
        if key not in twoHandMatchupDict:
            handAnalysis = classes.TwoHandMatchupAnalysis()
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
    print("Generating two hand winrate analysis")

    twoHandWinRateDict = {}

    twoHandBattles = getUseableTwoHandBattles(battles)

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        key1 = battle.hands[0].card1.unitType + "/" + battle.hands[0].card2.unitType
        key2 = battle.hands[1].card1.unitType + "/" + battle.hands[1].card2.unitType

        for key in [ key1, key2 ]:
            if key not in twoHandWinRateDict:
                handAnalysis = classes.TwoHandwinRateAnalysis()
                handAnalysis.key = key
                twoHandWinRateDict[key] = handAnalysis
            if (battle.hands[0].won and battle.hands[1].won):
                twoHandWinRateDict[key].outcomes.append(0.5)
            elif (battle.hands[0].won):
                twoHandWinRateDict[key].outcomes.append(1 if key == key1 else 0)
            else:
                twoHandWinRateDict[key].outcomes.append(0 if key == key1 else 1)

    # Derive a score based on outcomes
    for key in twoHandWinRateDict:
        twoHandWinRateDict[key].score = sum(twoHandWinRateDict[key].outcomes) / len(twoHandWinRateDict[key].outcomes)

    return twoHandWinRateDict

# Generate dictionary of outcomes by Unit
def generateUnitWinRatesAnalysis(battles):
    print("Generating unit winrate analysis")

    unitWinRateDict = {}

    twoHandBattles = getUseableTwoHandBattles(battles)

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        keys = []
        keys.append(battle.hands[0].card1.unitType)
        keys.append(battle.hands[0].card2.unitType)
        keys.append(battle.hands[1].card1.unitType)
        keys.append(battle.hands[1].card2.unitType)

        for key in keys:
            if key not in unitWinRateDict:
                handAnalysis = classes.UnitWinRateAnalysis()
                handAnalysis.key = key
                unitWinRateDict[key] = handAnalysis
            if (battle.hands[0].won and battle.hands[1].won):
                unitWinRateDict[key].outcomes.append(0.5)
            elif (battle.hands[0].won):
                if key in {card.unitType for card in [ battle.hands[0].card1, battle.hands[0].card2 ]}:
                    unitWinRateDict[key].outcomes.append(1)
                else:
                    unitWinRateDict[key].outcomes.append(0)
            else:
                if key in {card.unitType for card in [ battle.hands[0].card1, battle.hands[0].card2 ]}:
                    unitWinRateDict[key].outcomes.append(0)
                else:
                    unitWinRateDict[key].outcomes.append(1)

    # Derive a score based on outcomes
    for key in unitWinRateDict:
        unitWinRateDict[key].score = sum(unitWinRateDict[key].outcomes) / len(unitWinRateDict[key].outcomes)

    return unitWinRateDict

def getUseableTwoHandBattles(battles):
    return [battle for battle in battles if len(battle.hands) == 2 and battle.resolved]