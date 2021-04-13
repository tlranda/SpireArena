# Custom Libraries
import arena, monsters
# Builtin Libraries
from argparse import ArgumentParser as AP
# Possible Dependencies
import numpy as np

num_groups = 0

def build():
	prs = AP()
	prs.add_argument('-group', type=str, default=[], nargs="+", action="append", help="Filenames defining monster groups to fight")
	return prs

def parse(prs, args=None):
	if args is None:
		args = prs.parse_args()
	else:
		print(f"No interactive args yet")
	# Fixup args
	args.group = list(np.asarray(args.group).flatten())
	return args

def MakeMonsterFromString(string, battlefield=None, monsterGroup=None):
	line = string.rstrip().split()
	monsterType = line[0]
	monsterMaker = {'ID': line[1],
					'Arena': battlefield,
					'Friendlies': monsterGroup
					}
	monsterMaker.update(dict((k,v) for k,v in zip(line[2::2], line[3::2])))
	return monsters.makeMonster(monsterType, **monsterMaker)

def MakeMonsterGroupFromFile(fh, battlefield, ID=None):
	if ID is None:
		global num_groups
		ID = f"Group_{num_groups}"
		num_groups += 1
	monsterGroup = arena.MonsterGroup([], ID=ID)
	for line in fh.readlines():
		"""
			File format:
				One monster definition per line
				Fields are space-delimited
				First field is monster type (string matching class name)
				Second field is monster subid (distinguish in output)
				Beyond that should be pairs of elements such that the first is the keyword and the second is the value
					Class Constructors are required to properly convert strings to the intended data type for such inputs
		"""
		monsterGroup.AddMonster(MakeMonsterFromString(line, battlefield, monsterGroup), ephemeral=False)
	battlefield.AddGroup(monsterGroup)

"""
	Then basically want a statistician class to take an Arena and fight it # times, tracking which group is winning and make nice outputs based on that
	Ideally the statistician can listen to all the groups and/or monsters individually to track block/health/damage give/take too
"""

if __name__ == '__main__':
	args = parse(build())
	# Make groups
	colliseum = arena.Arena()
	for combat_group in args.group:
		with open(combat_group, 'r') as f:
			MakeMonsterGroupFromFile(f, colliseum)
	winner = colliseum.Brawl()

