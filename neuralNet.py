import tensorflow as tf
import classes

def convertBattlesIntoTrainingData(battles):
    unitTypes = []
    
    for battle in battles:
        for hand in battle.hands:
            if hand.card1.unitType not in unitTypes:
                unitTypes.append(hand.card1.unitType)
            if hand.card2.unitType not in unitTypes:
                unitTypes.append(hand.card2.unitType)
    
    unitTypes = sorted(unitTypes)

    inputLayerConverter = classes.InputLayerConverter(unitTypes)

    exampleTuples = []
    labelTuples = []

    for battle in battles:
        exampleTuple, labelTuple = inputLayerConverter.convertBattleIntoTuples(battle)
        exampleTuples.append(exampleTuple)
        labelTuples.append(labelTuple)

    # print(exampleTuples)
    # print(labelTuples)
