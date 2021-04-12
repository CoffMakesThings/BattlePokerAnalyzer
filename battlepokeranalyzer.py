import sys
import json
import os
from pprint import pprint
import configuration
import helperMethods
import classes
import multiprocessing as mp
from tqdm import tqdm
# import tensorflow as tf
import pickle
import gzip

if __name__ == "__main__":
    battles = []

    replaysProcessed = 0

    if configuration.generateNewBattles:
        # Copy sample replays into processing folder
        helperMethods.prepareProcessingDirectory()

        # Multithreading pool
        pool = mp.Pool()

        # Iterate through replays to collect all the battles
        print("\nGenerating battles from replays")

        fileNames = os.listdir(configuration.processingPath)
        filePaths = sorted({ configuration.processingPath + fileName for fileName in fileNames })
        filePaths = filePaths[0:configuration.maxFilesToAnalyze] # Chop down to desired amount

        for result in tqdm(pool.imap_unordered(helperMethods.analyzeFile, filePaths), total=len(filePaths)):
            battles += result
            replaysProcessed += 1

        pool.close()
        pool.join()

        # Pickle and zip battles
        print("Pickling and zipping battles")

        with gzip.open('battles.gz', 'wb') as output:
            pickle.dump(battles, output, pickle.HIGHEST_PROTOCOL)
    else:
        # Unzip and unpickle battles
        print("\nCollecting pickled battles")

        with gzip.open('battles.gz', 'rb') as input:
            battles = pickle.load(input)

    # Generate dictionary of scores of particular hand matchups
    twoHandMatchupDict = helperMethods.generateTwoHandMatchupAnalysis(battles)

    # Generate dictionary of scores of hands in any 2 hand battle
    twoHandWinRateDict = helperMethods.generateTwoHandwinRatesByHandAnalysis(battles)

    # Generate dictionary of scores of individual units in any 2 hand battle
    unitWinRateDict = helperMethods.generateUnitWinRatesAnalysis(battles)

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
        print(str(len(helperMethods.getUseableTwoHandBattles(battles))) + " useable two card battles remained")

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

    with open("WinRatesByIndividualUnit.csv", "w") as csv_file:
        sys.stdout = csv_file

        dictKeys = unitWinRateDict.keys()
        dictKeys = sorted(dictKeys, key=lambda dictKey: unitWinRateDict[dictKey].score)
        print('Unit,Battles,Winrate')
        for key in dictKeys:
            print('{},{},{}'.format(key, len(unitWinRateDict[key].outcomes), unitWinRateDict[key].score))

    sys.stdout = originalStdOut
    print("Process complete, find results in log and csv files")
