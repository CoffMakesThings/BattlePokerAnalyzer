import sys
import json
import os
from pprint import pprint
import configuration
import replaysProcessor
import classes
import multiprocessing as mp
from tqdm import tqdm
import pickle
import gzip
import lzma

if __name__ == "__main__":
    battles = []

    replaysProcessed = 0

    # Unzip and unpickle battles
    if configuration.loadBattlesFromFile:
        print("\nCollecting pickled battles")
        if configuration.loadBattlesFormat == 'lzma':
            with lzma.open('battles.xz', 'rb') as input:
                battles = pickle.load(input)
        if configuration.loadBattlesFormat == 'pkl':
            with open('battles.pkl', 'rb') as input:
                battles = pickle.load(input)
    else:
        # Generate new battles from replays
        print("\nGenerating battles from replays")

        # Copy sample replays into processing folder
        replaysProcessor.prepareProcessingDirectory()

        # Multithreading pool
        pool = mp.Pool()

        # Iterate through replays to collect all the battles
        fileNames = os.listdir(configuration.processingPath)
        filePaths = sorted({ configuration.processingPath + fileName for fileName in fileNames })
        filePaths = filePaths[0:configuration.maxFilesToAnalyze] # Chop down to desired amount

        for result in tqdm(pool.imap_unordered(replaysProcessor.analyzeFile, filePaths), total=len(filePaths)):
            battles += result
            replaysProcessed += 1

        pool.close()
        pool.join()

    # Pickle and zip battles
    if configuration.saveBattlesToFile:
        print("Pickling and zipping battles")
        if configuration.saveBattlesFormat == 'lzma':
            with lzma.open('battles.xz', 'wb') as output:
                pickle.dump(battles, output, pickle.HIGHEST_PROTOCOL)
        if configuration.saveBattlesFormat == 'pkl':
            with open('battles.pkl', 'wb') as output:
                pickle.dump(battles, output, pickle.HIGHEST_PROTOCOL)

    # Process analyses - See method comments for explanations
    twoHandMatchupDict = replaysProcessor.generateTwoHandMatchupAnalysis(battles)
    twoHandWinRateDict = replaysProcessor.generateTwoHandWinRatesByHandAnalysis(battles)
    unitWinRateDict = replaysProcessor.generateUnitWinRatesAnalysis(battles)
    unitMatchupDict = replaysProcessor.generateUnitMatchupAnalysis(battles)

    # Save current stdout
    originalStdOut = sys.stdout

    # Produce log file
    with open("output.log", "w") as log_file:
        # Log stats about how much data was used
        sys.stdout = log_file
        print("{} replays processed".format(replaysProcessed))
        print(str(len(battles)) + " total battles found")
        print(str(len([battle for battle in battles if battle.oneCard])) + " one card battles were excluded")
        print(str(len([battle for battle in battles if battle.wildcard])) + " battles with a wildcard were excluded")
        print(str(len([battle for battle in battles if not battle.resolved])) + " unresolved battles were excluded")
        print(str(len(replaysProcessor.getUseableTwoHandBattles(battles))) + " useable two card battles remained")

    # Produce csv files
    with open("TwoHandWinRatesByHand.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = twoHandWinRateDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandWinRateDict[dictKey].score)
        print('Hand,Battles,Winrate')
        for key in dictKeys:
            print('{},{},{}'.format(key, len(twoHandWinRateDict[key].outcomes), twoHandWinRateDict[key].score))

    with open("TwoHandMatchups.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = twoHandMatchupDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: twoHandMatchupDict[dictKey].score)
        print('Matchup,Battles,Winrate')
        for key in dictKeys:
            print('{},{},{}'.format(key, len(twoHandMatchupDict[key].outcomes), twoHandMatchupDict[key].score))

    with open("IndividualUnitWinRates.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = unitWinRateDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: unitWinRateDict[dictKey].score)
        print('Unit,Battles,Winrate')
        for key in dictKeys:
            print('{},{},{}'.format(key, len(unitWinRateDict[key].outcomes), unitWinRateDict[key].score))

    with open("IndividualUnitMatchups.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = unitMatchupDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: unitMatchupDict[dictKey].score)
        print('Unit,Battles,Winrate')
        for key in dictKeys:
            print('{},{},{}'.format(key, len(unitMatchupDict[key].outcomes), unitMatchupDict[key].score))

    with open("IndividualUnitMatchupsTabular.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = unitMatchupDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: unitMatchupDict[dictKey].score)

        unitKeys = [];

        for key in dictKeys:
            if (key.split(" vs ")[0] not in unitKeys):
                unitKeys.append(key.split(" vs ")[0]);
            if (key.split(" vs ")[1] not in unitKeys):
                unitKeys.append(key.split(" vs ")[1]);
        
        unitKeys = sorted(unitKeys)

        print("unit," + ",".join(unitKeys));
        for key in unitKeys:
            scores = [];

            for opponentKey in unitKeys:
                if key == opponentKey:
                    scores.append("{}".format(0.5));
                else:
                    # Find the matching dictionary key of the fight (eg. Archon vs Zergling)
                    matchingDictKeys = [x for x in dictKeys if key in x and opponentKey in x];
                    if len(matchingDictKeys) == 0:
                        scores.append("{}".format(""));
                    elif matchingDictKeys[0].index(key) == 0:
                        scores.append("{}".format(unitMatchupDict[matchingDictKeys[0]].score));
                    else:
                        scores.append("{}".format(1 - unitMatchupDict[matchingDictKeys[0]].score));

            print(key + "," + ",".join(scores));

    sys.stdout = originalStdOut
    print("Process complete, find results in log and csv files")
