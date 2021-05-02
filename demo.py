#!/usr/env/python3
import SpireArenaLib as SAL
from time import perf_counter as clock

"""
	Demonstrates usage patterns while also functioning
	as a test suite
	For detailed usage information: python3 demo.py -h
"""

# Automate test case switching a bit
from argparse import ArgumentParser as AP
def build():
	prs = AP()
	testIDs = [0,1,2]
	prs.add_argument("testID", type=int, choices=testIDs, help=f"Test to perform amongst {testIDs}")
	prs.add_argument('-debug', default=SAL.settings.ARENA_DEBUG, choices=list(SAL.settings.debug_names.keys()), help=f"Debug output level (default: {SAL.settings.reverse_debug_names[SAL.settings.ARENA_DEBUG]})")
	prs.add_argument("-turns", "-max-turns", type=int, default=1, help="Turns to demonstrate (default 1)")
	return prs
def parse(prs, args=None):
	args = prs.parse_args()
	return args

# Primary loop for all tests to execute
def demo(battlefield, turns):
	for _ in range(turns):
		battlefield.Turn()
	print("OUTPUT FROM demo.py::")
	print(battlefield)
	for group in battlefield.groups:
		print(group)

if __name__ == '__main__':
	args = parse(build())
	test = args.testID
	SAL.settings.ARENA_DEBUG = SAL.settings.debug_names[args.debug]
	start = clock()
	if test == 0:
		"""
			This pattern creates monsters first, then assigns them to groups
			using list slices during the Arena construction

			This is a code-efficient pattern for static assignment
		"""
		monster_pool = [SAL.makeMonster(**{'MonsterType': 'AcidSlime', 'ID': f"slime_{str(uid)}"}) for uid in range(1,3)]
		field = SAL.Arena(ID="SpireArena", groups=\
								[SAL.MonsterGroup(ID="GroupA", monsters=monster_pool[:1]),
						 		 SAL.MonsterGroup(ID="GroupB", monsters=monster_pool[1:])])
	elif test == 1:
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
	elif test == 2:
		"""
			Demonstrate that block works by forcing a Jaw Worm to use Thrash and getting hit back
		"""
		monster_pool = [SAL.makeMonster(**{'MonsterType': mType, 'ID': f'{mType}{str(uid)}'}) for mType, uid in zip(['JawWorm', 'AcidSlime'], range(1,3))]
		jawWorm, acidSlime = monster_pool
		field = SAL.Arena(ID='BlockArena', groups=[SAL.MonsterGroup(ID="GroupA", monsters=monster_pool[:1]),
												   SAL.MonsterGroup(ID="GroupB", monsters=monster_pool[1:])])
		# Manually invoke Thrash to test behavior:
		"""
		print(f"--MANUAL CONTROL--")
		thrashIndex = jawWorm.Callbacks.index(jawWorm.Thrash)
		print(f"Index {type(thrashIndex)} = {thrashIndex}")
		ability = jawWorm.Abilities[thrashIndex]
		print(f"Ability {type(ability)} = {ability}")
		move = jawWorm.MoveSelect(ability)
		print(f"Move {type(move)} = {move}")
		"""
		move = jawWorm.MoveSelect(jawWorm.Abilities[jawWorm.Callbacks.index(jawWorm.Thrash)])
		move.callback()
		#print(f"Move performed")
		#print(f"JawWorm powers = {jawWorm.PowerPool}")
		# Manually invoke a damaging attack to test block:
		acidSlime.MoveSelect(acidSlime.Abilities[acidSlime.Callbacks.index(acidSlime.Tackle)]).callback()
		acidSlime.MoveSelect(acidSlime.Abilities[acidSlime.Callbacks.index(acidSlime.Tackle)]).callback()
		acidSlime.MoveSelect(acidSlime.Abilities[acidSlime.Callbacks.index(acidSlime.Tackle)]).callback()
		acidSlime.MoveSelect(acidSlime.Abilities[acidSlime.Callbacks.index(acidSlime.Tackle)]).callback()
	else:
		raise ValueError(f"test has value {test}, valid values are {VALID_VALUES}")
	demo(field, args.turns)
	end = clock()
	print(f"Elapsed time: {end-start}")

