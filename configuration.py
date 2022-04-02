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
maxFilesToAnalyze = 9999999

# Pull replays from these directories
replayDirectories = [
    'Replays/AMDG/',
    'Replays/BotD/',
    'Replays/Sunxia/',
    'Replays/Coff/',
    'Replays/Kira/'
    # 'Replays/Test/'
    # 'Replays/New/'
]

# Analyze replays in this relative directory
processingPath = 'processing/'

# Units at this y coordinate or more are avatar units
lowestAvatarUnitYCoordinate = 84

# If false, analyzer will use pickled battles from previously loaded replays
loadBattlesFromFile = True
saveBattlesToFile = False

# Format to save and load battles in - Either lzma or pkl - lzma is slower but makes a smaller file
saveBattlesFormat = 'pkl'
loadBattlesFormat = 'pkl'

maxAmountByUnitType = {
    'Adept': 25,
    'Archon': 12,
    'Baneling': 100,
    'Banshee': 17,
    'BattleHellion': 25,
    'Battlecruiser': 8,
    'BroodLord': 12,
    'Carrier': 8,
    'Colossus': 8,
    'Corruptor': 25,
    'Cyclone': 17,
    'DarkTemplar': 25,
    'Drone': 100,
    'Ghost': 25,
    'Hellion': 25,
    'HighTemplar': 25,
    'Hydralisk': 25,
    'Immortal': 12,
    'Infestor': 25,
    'Liberator': 17,
    'LiberatorAG': 17,
    'Lurker': 17,
    'LurkerBurrowed': 17,
    'Marauder': 25,
    'Marine': 50,
    'Medivac': 50,
    'Mothership': 1,
    'Mutalisk': 25,
    'Oracle': 17,
    'Overlord': 100,
    'Phoenix': 25,
    'Probe': 100,
    'Queen': 25,
    'Ravager': 17,
    'Raven': 25,
    'Reaper': 50,
    'Roach': 25,
    'SCV': 100,
    'SiegeTank': 17,
    'SiegeTankSieged': 17,
    'Stalker': 25,
    'SwarmHost': 17,
    'SwarmHostBurrowed': 17,
    'Tempest': 10,
    'Thor': 8,
    'ThorAP': 8,
    'Ultralisk': 8,
    'Viking': 25,
    'VikingAssault': 25,
    'VoidRay': 12,
    'WidowMine': 25,
    'WidowMineBurrowed': 25,
    'Zealot': 25,
    'Zergling': 100
}