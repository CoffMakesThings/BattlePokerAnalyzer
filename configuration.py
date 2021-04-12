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
maxFilesToAnalyze = 999999

# Pull replays from these directories
replayDirectories = [
    'Replays/AMDG/',
    'Replays/BotD/',
    'Replays/Sunxia/',
    'Replays/Coff/',
    # 'Replays/Test/'
]

# Analyze replays in this relative directory
processingPath = 'processing/'

# Units at this y coordinate or more are avatar units
lowestAvatarUnitYCoordinate = 84