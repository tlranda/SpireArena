#!/usr/env/python3
import SpireArenaLib as SAL

"""
	Demonstrates usage patterns while also functioning
	as a test suite
	For detailed usage information: python3 demo.py -h
"""

# Automate test case switching a bit
from argparse import ArgumentParser as AP
def build():
	prs = AP()
	testIDs = [0,1]
	prs.add_argument("testID", type=int, choices=testIDs, help=f"Test to perform amongst {testIDs}")
	prs.add_argument("-no-debug", action="store_true", help=f"See if you can rip off debug bandaid")
	return prs
def parse(prs, args=None):
	args = prs.parse_args()
	return args

# Primary loop for all tests to execute
def demo(battlefield):
	for _ in range(1):
		battlefield.Turn()
	print(battlefield)
	for group in battlefield.groups:
		print(group)

if __name__ == '__main__':
	args = parse(build())
	constructor_pattern = args.testID
	if args.no_debug:
		SAL.settings.ARENA_DEBUG = False
	if constructor_pattern == 0:
		"""
			This pattern creates monsters first, then assigns them to groups
			using list slices during the Arena construction

			This is a code-efficient pattern for static assignment
		"""
		monster_pool = [SAL.makeMonster(**{'MonsterType': 'AcidSlime', 'ID': f"slime_{str(uid)}"}) for uid in range(1,3)]
		field = SAL.Arena(ID="SpireArena", groups=\
								[SAL.MonsterGroup(ID="GroupA", monsters=monster_pool[:1]),
						 		 SAL.MonsterGroup(ID="GroupB", monsters=monster_pool[1:])])
		demo(field)
	elif constructor_pattern == 1:
		"""
			This pattern creates the arena first, then groups to assign monsters
			to and finally adds monsters to specific groups

			Likely a better pattern for dynamic assignment where the group count
			and/or monster count are variable
		"""
		field = SAL.Arena(ID="SpireArena")
		groups = [SAL.MonsterGroup(ID="Group"+chr(65+_)) for _ in range(2)]
		field.AddGroups(*groups)
		for group, name in zip(groups, [str(uid) for uid in range(1,len(groups)+1)]):
			group.AddMonsters(False,
							  SAL.makeMonster(**{'MonsterType': 'AcidSlime',\
												'ID': f"slime_{name}",\
												'Arena':field,\
												'Friendlies':group}))
		demo(field)
	else:
		raise ValueError(f"constructor_pattern on line 5 has value {constructor_pattern}, valid values are {VALID_VALUES}")


