import tensorflow as tf

def convertBattlesIntoTrainingData(battles):
    unitTypes = []
    
    for battle in battles:
        for hand in battle.hands:
            if hand.card1.unitType not in unitTypes:
                if hand.card1.maxAmount == 50:
                    print(hand.card1.unitType)
                unitTypes.append(hand.card1.unitType)
            if hand.card2.unitType not in unitTypes:
                if hand.card2.maxAmount == 50:
                    print(hand.card2.unitType)
                unitTypes.append(hand.card2.unitType)
    
    unitTypes = sorted(unitTypes)

    print(unitTypes)
