import classes
import random
import torch
import torch.nn as nn
import torch.optim as optim

def trainStep(model, lossFn, optimizer, x, y):
    # Sets model to TRAIN mode
    model.train()
    # Makes predictions
    prediction = model(x)
    # Computes loss
    loss = lossFn(y, prediction)
    # Computes gradients
    loss.backward()
    # Updates parameters and zeroes gradients
    optimizer.step()
    optimizer.zero_grad()
    # Returns the loss
    return loss.item()

def getModelFromBattles(battles):
    print("\nGenerating CNN tuples from battles\n")
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

    random.shuffle(exampleTuples)
    random.shuffle(labelTuples)

    print("\nTuples made, creating CNN\n")

    xTensor = torch.tensor(exampleTuples).float()
    yTensor = torch.tensor(labelTuples).float()

    # train_examples = exampleTuples[:len(exampleTuples)//2]
    # train_labels = labelTuples[:len(labelTuples)//2]
    # test_examples = exampleTuples[len(exampleTuples)//2]
    # test_labels = labelTuples[len(labelTuples)//2]

    inputSize = len(unitTypes) * 2
    hiddenSize = len(unitTypes)
    outputSize = 2

    model = nn.Sequential(nn.Linear(inputSize, hiddenSize),
                      nn.ReLU(),
                      nn.Linear(hiddenSize, outputSize),
                      nn.Softmax(dim=1))

    lr = 1e-6
    lossFn = nn.MSELoss(reduction='sum')
    optimizer = optim.SGD(model.parameters(), lr=lr)

    epochs = 1000
    losses = []

    # For each epoch...
    for epoch in range(epochs):
        # Performs one train step and returns the corresponding loss
        loss = trainStep(model, lossFn, optimizer, xTensor, yTensor)
        losses.append(loss)

    print(model.state_dict())

    print("Test")
    
    mockBattle = classes.Battle()
    card1 = classes.Card()
    card1.amount = 8
    card1.unitType = "Carrier"
    card2 = classes.Card()
    card2.amount = 100
    card2.unitType = "Baneling"
    card3 = classes.Card()
    card3.amount = 5
    card3.unitType = "Marine"
    card4 = classes.Card()
    card4.amount = 5
    card4.unitType = "Reaper"
    hand1 = classes.Hand()
    hand1.card1 = card1
    hand1.card2 = card2
    hand2 = classes.Hand()
    hand2.card1 = card3
    hand2.card2 = card4
    mockBattle.hands.append(hand1)
    mockBattle.hands.append(hand2)

    mockX, mockY = inputLayerConverter.convertBattleIntoTuples(mockBattle)

    mockXTensor = torch.tensor([mockX]).float()

    testPrediction = model(mockXTensor)
    print(testPrediction)

    # print(exampleTuples)
    # print(labelTuples)
