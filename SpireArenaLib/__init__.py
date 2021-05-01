import sys, os
# Ensure that these relative imports work regardless of where the SpireArenaLib directory is located
HOME=os.path.dirname(os.path.abspath(__file__))
#print(HOME)
sys.path.append(HOME)
# Library
from arena import MonsterGroup, Arena
#print("Arena import success")
from monsters import MonsterMove, Monster, makeMonsterFromString, makeMonsterGroupFromFile, makeMonster
#print("Monsters import success")
from powers import SOURCE, TRIGGER, DESCRIPTIONS, Power, makePower
#print("Powers import success")
import settings
#print("Settings import success")

# Restore sys.path to is previous status and clean up module
sys.path.remove(HOME)
del HOME, sys, os
