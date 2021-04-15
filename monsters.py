# Arena API is not needed for monsters, but single source of RNG is needed
from arena import global_rng
# Need access to the entire powers API and all of their enums
from powers import *

"""
	TODO:
		Make Monster.Alive a property or lambda or something?
		Make monsters have a GainBlock() function similar to damage (can grant block to others too a la Shield Gremlin)
			Make sure the block from GainBlock reduces HP damage and triggers proper power triggers etc etc etc
"""

"""
#0 MonsterMove (Abstract)
	Defines a particular monster move
	Given a class, callback, and string-able attributes
"""
class MonsterMove():
	def __init__(self, affectClass, callback, description="<No move description provided>"):
		self.affectClass = affectClass
		self.callback = callback
		self.ID = callback.__name__
		self.description = description

	def __str__(self):
		return f"{self.ID} defined as {self.description}"

"""
#1 Monster (Abstract)
	Defines a particular Spire abomination

	Subclasses are named entities that fully implement their particular movesets, stats, patterns, ascension behaviors, etc
"""
class Monster():
	def __init__(self, ID="<TemplateMonster>", Arena=None, Friendlies=None):
		"""
			ATTRIBUTES:
				* ID (str, debug)
				* Arena (arena.Arena reference)
				* Friendlies (arena.MonsterGroup reference for allied block)
				* rng (random.RandomState for RNG)
				* Name (str, flavor)
				* Act (int, flavor)
				* Abilities (list of callable functions to perform attacks)
				* Pattern (list of weights to probabilistically sample an action from)
				* Ascension (int: this monster is at ascension X)
				* MaxHealth, Health, Block, Strength, Dexterity (integers)
				* Alive (bool)
					* When this gets flipped off, tell Friendly group to -= 1 it's fight_on
					* When this gets turned back on, tell Friendly group to += 1 it's fight_on
				* PowerPool (list of callable PowerObjects that implement listeners to adjust effects)
					* All PowerPool'd objects can be called before, during, and after doing basically anything
				* History (list of Ability usages to enforce intent rules)
		"""
		self.ID = ID
		self.Arena = Arena
		self.Friendlies = Friendlies
		self.rng = global_rng
		self.Name, self.Act, self.ascension = "<GenericMonster>", 0, 0
		self.MaxHealth, self.Health, self.Block = 0, 0, 0
		self.PowerPool, self.Pattern, self.Abilities, self.Callbacks = [], [], [], []
		self.History, self.HistoryIdx = [], 0
		self.Alive = True

	def __str__(self):
		string = f"{self.Name} {self.ID}"
		if self.Friendlies is not None:
			string = f"{str(self.Friendlies)}::{string}"
		if self.Arena is not None:
			string = f"{str(self.Arena)}::{string}"
		return string

	def Reset(self):
		self.Health = self.MaxHealth
		self.Alive = True
		self.PowerPool = []
		self.History = []
		self.HistoryIdx = 0
		if not self.Alive and self.Friendlies is not None:
			self.Friendlies.fight_on += 1

	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		"""
			No special intents by default
		"""
		print(f"{self.Name}'s move is not overridden by template class's SpecialIntent()")
		return moveCall, moveAlternatives, moveChances

	def MoveSelect(self, move=None):
		"""
			Return the move or result from pruned array if history rejects the intended move
		"""
		if move is None:
			move = self.rng.choices(self.Abilities, weights=self.Pattern, k=1)[0]
		# Special History rejection
			# Does not return modified ability/probability list as it is either unchanged
			# (default history check uses this given list) or it was changed (ergo default
			# history check won't trigger)
		move_idx = self.Callbacks.index(move.callback)
		not_move_sum = sum(self.Pattern) - self.Pattern[move_idx]
		remainingMoves = [_ for idx, _ in enumerate(self.Abilities) if idx != move_idx]
		remainingChances = [_/not_move_sum for idx, _ in enumerate(self.Pattern) if idx != move_idx]
		# This call to be overridden by implementing classes
		move = self.SpecialIntent(move, remainingMoves, remainingChances)
		move_idx = self.Callbacks.index(move.callback)
		# Normal History rejection (x3 never allowed)
		if len(self.History) == 2 and sum(self.History)/2 == float(move_idx):
			move = self.rng.choices(remainingMoves, weights=remainingChances, k=1)[0]
			move_idx = self.Callbacks.index(move.callback)
		# Record history
		if len(self.History) < 2:
			self.History.append(move_idx)
		else:
			self.History[self.HistoryIdx] = move_idx
		self.HistoryIdx = (self.HistoryIdx + 1) % 2
		return move

	def Turn(self, move=None):
		if self.Alive:
			move = self.MoveSelect(move)
			"""
			print(f"{str(self)} performs {str(move)}; history is "
				  f"{[self.Callbacks[self.History[(self.HistoryIdx-_)%2]].__name__ for _ in range(len(self.History),0,-1)]}")
			"""
			move.callback()
		else:
			print(f"{str(self)} is dead. Skipping turn")

	def Empower(self, value, source_class, *trigger_classes, source, target, extras=[]):
		"""
			Alter value using self.PowerPool based on trigger_class and source_class
		"""
		powerQueue = []
		for power in self.PowerPool:
			for trigger in trigger_classes:
				if trigger in power.triggers:
					powerQueue.append(power)
					break
		# Sort powerQueue by priority
		powerQueue = sorted(powerQueue, key=lambda x: x.priority, reverse=True)
		# Activate powers
		for power in powerQueue:
			new_value = power.Affect(value, source_class, source, target, extras)
			print("\t"+f"{str(self)}'s {power} updates value from {value} to {new_value}")
			value = new_value
		return value

	def Select(self, ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True):
		"""
			Use generator functions Affect() to get monsters affected and for each damage instance, run it through all participants relevant powers
			after the affect, run through both targets post powers based on the ultimate outcome
		"""
		# Get all the candidate groups
		arenaGroups = [[val for val in self.Arena.Affect(self.Friendlies, IncludeSelf=ArenaSelf, All=ArenaAll)] for _ in range(ArenaTargets)]
		# Determine number of targets to pick
		maxTargeted = sum([_[0] for _ in arenaGroups])
		if ArenaTargets is not None:
			maxTargeted = min(ArenaTargets, maxTargeted)
		# Make actual groups
		targetedGroups = []
		for groupList in arenaGroups:
			targetedGroups.extend(groupList[1:])
		if ArenaTargets is not None:
			# Randomly target groups up to the number of targets
			targetedGroups = self.rng.choices(targetedGroups, k=ArenaTargets)

		# Now select group targets in each group
		monsterGroups = [[val for val in group.Affect(self, GroupOnlySelf, GroupIncludeSelf, GroupAll, GroupCheckAlive)] for group in targetedGroups]
		# Refine number of targets to pick
		maxTargeted = sum([_[0] for _ in monsterGroups])
		if GroupTargets is not None:
			maxTargeted = min(GroupTargets, maxTargeted)
		# Make actual targets
		targetedMonsters = []
		for monsterList in monsterGroups:
			targetedMonsters.extend(monsterList[1:])
		if GroupTargets is not None:
			# Randomly target monsters across groups up to the number of targets
			targetedMonsters = self.rng.choices(targetedMonsters, k=GroupTargets)
		# Return the targeted Monsters
		return targetedMonsters

	def ApplyPowers(self, *powers, affectClass=SOURCE.SKILL,
				ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
				extras=[]):
		"""
			CALL FROM THE OBJECT APPLYING THE POWERS
			powers = list of Power objects to add to the target Objects
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if this application triggers any other powers
			others specify how to locate targets for the power application
		"""
		targets = self.Select(ArenaTargets=ArenaTargets, ArenaSelf=ArenaSelf, ArenaAll=ArenaAll,
				GroupTargets=GroupTargets, GroupOnlySelf=GroupOnlySelf, GroupIncludeSelf=GroupIncludeSelf, GroupAll=GroupAll, GroupCheckAlive=GroupCheckAlive)
		enemies = self.Select(ArenaTargets=1, ArenaSelf=False, ArenaAll=True,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=GroupCheckAlive)
		Powers = [[TRIGGER.ON_POWER_GAIN], [TRIGGER.VS_POWER_GAIN]]
		# Iteratively push powers but push them all at once to allow multipower applications to count as one for power trigger reasons
		for target in targets:
			target.PowerPool.extend(powers)
			# React to power change
			if target == self:
				self.Empower(powers, affectClass, *Powers[0], source=self, target=self)
				# Allies and self don't get VS triggers
				for enemy in enemies:
					enemy.Empower(powers, affectClass, *Powers[1], source=self, target=self, extras=extras)
			else:
				target.Empower(powers, affectClass, *Powers[0], source=self, target=target, extras=extras)
				targets_enemies = target.Select(ArenaTargets=1, ArenaSelf=False, ArenaAll=True,
								GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=GroupCheckAlive)
				for target_enemy in targets_enemies:
					# Allies of the target and the target itself don't get VS triggers
					target_enemy.Empower(powers, affectClass, *Powers[1], source=self, target=target, extras=extras)
		# Return targets for logging
		return targets

	def Damage(self, *amounts, empowerDamage=True, affectClass=SOURCE.ATTACK,
				ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
				extras=[]):
		"""
			CALL FROM THE OBJECT DEALING THE DAMAGES
			amounts = list of damage values to produce (affected by powers)
			empowerDamage determines if powers apply to the damage instance (either both ways or no ways)
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if powers interact differently
			others specify how to locate targets for the damage instance
		"""
		targets = self.Select(ArenaTargets=ArenaTargets, ArenaSelf=ArenaSelf, ArenaAll=ArenaAll,
				GroupTargets=GroupTargets, GroupOnlySelf=GroupOnlySelf, GroupIncludeSelf=GroupIncludeSelf, GroupAll=GroupAll, GroupCheckAlive=GroupCheckAlive)
		# Iteratively perform damage
		dealt = []
		for damage in amounts:
			dealt.append(0)
			# Can stop multiattacks early etc if die during the effect
			if self.Alive:
				for target in targets:
					if empowerDamage:
						Powers = [[TRIGGER.OFFENSE], [TRIGGER.DEFENSE]]
						if affectClass == SOURCE.ATTACK:
							Powers[0].append(TRIGGER.ON_ATTACK)
							Powers[1].append(TRIGGER.VS_ATTACK)
						elif affectClass == SOURCE.SKILL:
							Powers[0].append(TRIGGER.ON_SKILL)
							Powers[1].append(TRIGGER.VS_SKILL)
						elif affectClass == SOURCE.TRIGGER:
							Powers[0].append(TRIGGER.ON_POWER_GAIN)
							Powers[1].append(TRIGGER.VS_POWER_GAIN)
						# First you get to empower your damage
						damage = self.Empower(damage, affectClass, *Powers[0], source=self, target=target, extras=extras)
						# Then the target empowers the damage
						damage = target.Empower(damage, affectClass, *Powers[1], source=self, target=target, extras=extras)
					# Now that damage has been affected and side effects taken care of by powers, deal the damage
					# Anything less than 0 damage is 0 damage
					damage = max(0, damage)
					target_was_alive = target.Alive
					target.Health -= damage
					dealt[-1] += damage
					# Now call post damage powers
					Powers = [[TRIGGER.AFTER_ATTACK],[TRIGGER.AFTER_ATTACK_ED]]
					if damage > 0:
						Powers[0].append(TRIGGER.VS_HP_REDUCE)
						Powers[1].append(TRIGGER.ON_HP_REDUCE)
					if target_was_alive and not target.Alive:
						Powers[0].append(TRIGGER.ON_KILL)
						Powers[1].append(TRIGGER.ON_DEATH)
					self.Empower(damage, affectClass, *Powers[0], source=self, target=target, extras=extras)
					target.Empower(damage, affectClass, *Powers[1], source=self, target=target, extras=extras)
		# Return damage dealt for logging
		return dealt, targets

	def makeMoves(self, *move_tuples):
		self.Callbacks = []
		self.Abilities = []
		for move in move_tuples:
			self.Callbacks.append(move[1])
			self.Abilities.append(MonsterMove(*move))

# Routine to contruct monsters based on one-line, space-delimited strings
def MakeMonsterFromString(string, battlefield=None, monsterGroup=None):
	line = string.rstrip().split()
	monsterType = line[0]
	monsterMaker = {'ID': line[1],
					'Arena': battlefield,
					'Friendlies': monsterGroup
					}
	monsterMaker.update(dict((k,v) for k,v in zip(line[2::2], line[3::2])))
	return makeMonster(monsterType, **monsterMaker)

# Routine to create monster groups from a text file (1-monster-per-line), with static default group counting
num_groups = 0
def MakeMonsterGroupFromFile(fh, battlefield, ID=None):
	if ID is None:
		global num_groups
		ID = f"Group_{num_groups}"
		num_groups += 1
	monsterGroup = arena.MonsterGroup(monsters=[], ID=ID)
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
	battlefield.AddGroups(monsterGroup)
	return monsterGroup

# Routine to locate a monster constructor from any act based on the monster name
objects = {}
# These imports WILL include importing this file, but so long as the needed class definitions are higher than this it should be OK
import act_1_monsters as a1
objects.update(a1.objects())
#import act_2_monsters as a2
#objects.update(a2.objects())
#import act_3_monsters as a3
#objects.update(a3.objects())
#import act_4_monsters as a4
#objects.update(a4.objects())
def makeMonster(Type, **kwargs):
	return objects[Type](**kwargs)

