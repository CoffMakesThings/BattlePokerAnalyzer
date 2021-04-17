import os
import configuration
import shutil
import sc2reader
import classes
from pprint import pprint

# Move all replays from the replays folders into the processing folder, renamed such that they dont overwrite each other
def prepareProcessingDirectory():
    print("Preparing processing folder\n")
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

# Useful for investigating what is available in sc2reader
def printEventsOfReplay(replay):
    with open("replay_root.log", "w") as log_file:
        pprint(vars(replay), log_file)

    with open("replay_game_events.log", "w") as log_file:
        for message in vars(replay)['raw_data']['replay.game.events']:
            pprint(vars(message), log_file)

    with open("replay_tracker_events.log", "w") as log_file:
        for message in vars(replay)['raw_data']['replay.tracker.events']:
            pprint(vars(message), log_file)

    with open("replay_message_events.log", "w") as log_file:
        for message in vars(replay)['raw_data']['replay.message.events']['messages']:
            pprint(vars(message), log_file)

    with open("replay_attributes_events.log", "w") as log_file:
        for message in vars(replay)['raw_data']['replay.attributes.events']:
            pprint(vars(message), log_file)

    with open("replay_messages.log", "w") as log_file:
        for message in vars(replay)['messages']:
            pprint(vars(message), log_file)

    with open("replay_message_events.log", "w") as log_file:
        for message in vars(replay)['message_events']:
            pprint(vars(message), log_file)

# Useful for debugging
def printBattles(battles):
    print("Printing {} battles".format(len(battles)))
    for battle in battles:
        print('\nBattle starting at {} ending at {}'.format(battle.startTime, battle.endTime))
        print('From {}'.format(battle.replay))
        print('{} oneCard'.format(battle.oneCard))
        print('{} wildcard'.format(battle.wildcard))
        print('{} resolved'.format(battle.resolved))
        for unitType in set({unit.name for unit in battle.units}):
            print('{} {}'.format(len([unit for unit in battle.units if unit.name is unitType]), unitType))

# Analyze one file and derive battles based on when units were created and died
def analyzeFile(filePath):
    # print("Processing replay at " + filePath)
    
    # Get all the unit birth/death events from sc2reader
    replay = sc2reader.load_replay(filePath, load_level=4)
    trackerEvents = vars(replay)['raw_data']['replay.tracker.events'];
    birthAndDeathEvents = [event for event in trackerEvents
                           if vars(event)['name'] == 'UnitDiedEvent' or vars(event)['name'] == 'UnitBornEvent']

    # Derive units from birth and death events
    units = []
    # print("Deriving units from replay events")

    for birthAndDeathEvent in birthAndDeathEvents:
        apiUnit = vars(vars(birthAndDeathEvent)['unit'])
        # Ignore avatar units
        if apiUnit['location'][1] < configuration.lowestAvatarUnitYCoordinate:
            # Ignore the unit if its in the ignored list (broodlings, etc)
            if apiUnit['_type_class'] is not None and not any(ignoredUnit == vars(apiUnit['_type_class'])['name'] for ignoredUnit in configuration.ignoredUnits):
                # Use unit id to check if this unit is already in our list
                if not any(unit.apiId == apiUnit['id'] for unit in units):
                    # This unit is valid and hasn't been added yet, add to list with all details
                    unit = classes.Unit()
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
    # print("Deriving battles from units")

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
            battle.replay = filePath
            battle.units.append(unit)
            battle.startTime = unit.createdTime
            if unit.diedTime is None:
                battle.resolved = False
            else:
                battle.endTime = unit.diedTime
            battles.append(battle)

    # Derive cards and hands from battles
    # print("Deriving cards and hands from battles")

    for battle in battles:
        if battle.resolved:
            # Detect battles with wildcards - Won't deal with wildcards for now
            unitTypes = {unit.name for unit in battle.units}
            owners = {unit.owner for unit in battle.units}
            # print("Battle starting at " + str(battle.startTime))

            for owner in owners:
                ownedUnits = [unit for unit in battle.units if unit.owner is owner]
                ownedUnitTypes = {unit.name for unit in ownedUnits}
                if (len(ownedUnitTypes) < 2):
                    battle.oneCard = True
                    break
                elif (len(ownedUnitTypes) > 2 or len(unitTypes) is not len(owners) * 2):
                    battle.wildcard = True
                    break

            if not battle.wildcard and not battle.oneCard:
                # Not a wildcard battle, let's derive cards
                cards = []

                for unitType in unitTypes:
                    card = classes.Card()
                    card.unitType = unitType
                    cardUnits = [unit for unit in battle.units if unit.name == unitType]
                    card.amount = len(cardUnits)
                    card.owner = cardUnits[0].owner
                    card.lastDeathTime = max(unit.diedTime for unit in cardUnits)
                    cards.append(card)

                # Now lets derive hands
                cards = sorted(cards, key=lambda card: card.unitType)
                for card in cards:
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
        
        # Clear units to reduce size of battles.pkl
        battle.units = None

    return battles

# Generate dictionary of outcomes by 2 hand battles
def generateTwoHandMatchupAnalysis(battles):
    print("Generating two hand matchup analysis")

    twoHandMatchupDict = {}

    twoHandBattles = getUseableTwoHandBattles(battles)

    print("Iterating two hand battles")

    for battle in twoHandBattles:
        if battle.hands[0].card1 is None or battle.hands[0].card2 is None or battle.hands[1].card1 is None or battle.hands[1].card2 is None:
            printBattles([battle])
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
    # Return all battles that meet the following conditions:
    # - Includes only two players
    # - Battle finished before game ended
    # - All units are property typed
    # - No wildcard units
    return [battle for battle in battles if len(battle.hands) == 2 and battle.resolved and not battle.wildcard and not battle.oneCard]