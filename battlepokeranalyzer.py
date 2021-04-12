import sys
import json
import os
from pprint import pprint
import configuration
import helperMethods
import classes

# Copy sample replays into processing folder
helperMethods.prepareProcessingDirectory()

battles = []

# Iterate through replays to collect all the battles
counter = 0
print("Iterating replays")

for file in os.listdir(configuration.processingPath):
    if counter < configuration.maxFilesToAnalyze:
        battles += helperMethods.analyzeFile(configuration.processingPath + file)
        counter += 1
        print(str(counter) + "/" + str(len(os.listdir(configuration.processingPath))) + " replays processed")

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
    print(str(len(battles)) + " total battles found")
    print(str(len([battle for battle in battles if battle.hasWildcard])) + " battles with wildcards were excluded")
    print(str(len([battle for battle in battles if not battle.resolved])) + " unresolved battles were excluded")
    print(str(len(helperMethods.getUseableTwoHandBattles(battles))) + " useable two hand battles remained")

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
