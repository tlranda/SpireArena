# Custom Libraries
from SpireArenaLib import arena, monsters, settings
# Builtin Libraries
from argparse import ArgumentParser as AP
# Possible Dependencies
import numpy as np

def build():
	prs = AP()
	prs.add_argument('-group', type=str, default=[], nargs="+", action="append", required=True, help="Filenames defining monster groups to fight")
	prs.add_argument('-seed', type=int, default=None, help="Set global RNG seed (default not set--psuedorandom)")
	prs.add_argument('-max-turns', '-turns', type=int, default=None, help="Limit turns in each brawl (default None)")
	prs.add_argument('-debug', default=settings.ARENA_DEBUG, choices=list(settings.debug_names.keys()), help=f"Debug output level (default: {settings.reverse_debug_names[settings.ARENA_DEBUG]})")
	return prs

def parse(prs, args=None):
	if args is None:
		args = prs.parse_args()
	else:
		print(f"No interactive args yet")
	# Fixup args
	args.group = list(np.asarray(args.group).flatten())
	return args

"""
	Then basically want a statistician class to take an Arena and fight it # times, tracking which group is winning and make nice outputs based on that
	Ideally the statistician can listen to all the groups and/or monsters individually to track block/health/damage give/take too
"""

if __name__ == '__main__':
	args = parse(build())
	settings.ARENA_DEBUG = settings.debug_names[args.debug]
	# Set seed as necssary
	if args.seed is not None:
		arena.global_rng.seed(args.seed)
	# Make groups
	colliseum = arena.Arena(ID="SpireArena")
	for combat_group in args.group:
		with open(combat_group, 'r') as f:
			monsters.makeMonsterGroupFromFile(f, colliseum)
	winner = colliseum.Brawl(args.max_turns)

