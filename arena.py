# Slay the Spire Arena: Pit mobs vs one another and fight it out to the death!
import random, enum
global_rng = random.Random()
from copy import deepcopy as dcpy
"""
Class Listing:
	PowerObject, Power* represent callbacks to modify events
	Monster represents a spire creature
	MonsterGroup represents a collection of aligned creatures
	Arena represents the fight itself
"""

"""
	Power Enum for what type of thing sources an effect
"""
class SOURCE(enum.Enum):
	ATTACK = 0
	SKILL = 1
	POWER = 2
	FX = 3

class POWER(enum.Enum):
	OFFENSE = 0
	DEFENSE = 1
	ON_DEATH = 2
	ON_KILL = 3
	ON_ATTACK = 4
	VS_ATTACK = 5
	ON_SKILL = 6
	VS_SKILL = 7
	ON_POWER_GAIN = 8
	VS_POWER_GAIN = 9
	ON_POWER_LOSE = 10
	VS_POWER_LOSE = 11
	ON_TURN = 12
	ON_HP_REDUCE = 13
	VS_HP_REDUCE = 14
	AFTER_ATTACK = 15
	AFTER_ATTACK_ED = 16

"""
#0 PowerObject (Abstract)
	Defines an API for events in the fight:
		* Timing variants for ALL (BEFORE, ON, AFTER) : When to accept the event occurring
	Instanceable Examples of Enum classes
		* OffensePowers
			# Priority Order: Strength (3), Shackles (2), Weak (1)
		* DefensePowers
			# Priority Order: Vulnerable (3), Intangible (2), Block (1)
		* UtilityPowers
			# On kill/death
				# FungiCombust
			# On/Vs attack/skill/power gain/power lose
				# Chosen Hex, Awoken Phase 1
			# On turn
				# Lagavulin, OrbWalker
			# On/Vs hp reduce
				# Transient
			# After attack(ed)
				# Malleable, Thorns

	ATTRIBUTES:
		turns : Int (turns to live) or None (permanent)
		priority : Int (higher # == higher priority)
		triggers : List of POWER classes to activate on
	METHODS:
		Affect(value, cardtype, owner, target, *extra) : Implements the callback for the effect; returns value as it should be affected while applying side affects to owner and target
		Prepare(*extra) : Prepares the next Affect call (optional)
		TurnTick() : Reduce power lifespan each turn
"""
class Power():
	"""
		Shell of a class, holds a list of enum values for when it activates, a duration (None for infinite) and a method callback fitting the Affect API:
			self, value, cardtype, owner, target, *extra
		The callback method should affect value appropriately to achieve the power's end goals, and is provided access to the effect owner and effect target to apply any necessary side effects

		A second callback is bound to the Prepare API (not used for all powers):
			self, *extra
		This should use variables in *extra tuple to set object internal state in preparation for future calls to Affect()

		TurnTick should be called at the end of every turn on all powers for everything, decrements powers as needed. Returns True when the power should be eliminated
	"""
	def __init__(self, timings, turns, callback, callback2=None):
		self.triggers = timings
		self.turns = turns
		self.Affect = callback
		if callback2 is not None:
			# Override self.Prepare()
			self.Prepare = callback2

	def Prepare(self, *extra):
		# Shell method takes anything and does nothing
		pass

	def TurnTick(self):
		# Make Powers have a lifespan
		if self.turns is not None:
			self.turns -= 1
			return self.turns == 0
		else:
			return False

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
		global global_rng
		self.rng = global_rng
		self.Name, self.Act, self.ascension = "<GenericMonster>", 0, 0
		self.MaxHealth, self.Health, self.Block, self.Strength, self.Dexterity = 0, 0, 0, 0, 0
		self.PowerPool, self.Pattern, self.Abilities = [], [], []
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
		not_move_sum = sum(self.Pattern) - self.Pattern[self.Abilities.index(move)]
		remainingMoves = [_ for _ in self.Abilities if _ != move]
		remainingChances = [_/not_move_sum for _, __ in zip(self.Pattern, self.Abilities) if __ != move]
		# This call to be overridden by implementing classes
		move = self.SpecialIntent(move, remainingMoves, remainingChances)
		move_idx = self.Abilities.index(move)
		# Normal History rejection (x3 never allowed)
		if len(self.History) == 2 and sum(self.History)/2 == float(move_idx):
			move = self.rng.choices(remainingMoves, weights=remainingChances, k=1)[0]
			move_idx = self.Abilities.index(move)
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
			print(f"{str(self)} performs {move.__name__}; history is {[self.Abilities[self.History[(self.HistoryIdx-_)%2]].__name__ for _ in range(len(self.History),0,-1)]}")
			move()
		else:
			print(f"{self} is dead. Skipping turn")

	def Empower(self, value, source_class, *trigger_classes, source, target):
		"""
			Alter value using self.PowerPool based on trigger_class and source_class
		"""
		powerQueue = []
		for power in self.PowerPool:
			for trigger in power.triggers:
				if trigger in trigger_classes:
					print(f"Trigger power {power}")
					powerQueue.append(power)
					break
		# Sort powerQueue by priority
		powerQueue = sorted(powerQueue, key=lambda x: x.priority, reverse=True)
		# Activate powers
		for power in powerQueue:
			new_value = power.Affect(value, source_class, source, target)
			print(f"{power} updates value from {value} to {new_value}")
			value = new_value
		return value

	def Select(self, ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True):
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

	def Damage(self, *amounts, empowerDamage=True, affectClass=SOURCE.ATTACK,
				ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True):
		"""
			CALL FROM THE OBJECT DEALING THE DAMAGES
			amounts = list of damage values to produce (affected by powers)
			empowerDamage determines if powers apply to the damage instance (either both ways or no ways)
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if powers interact differently
			others specify how to locate targets for the damage instance
				Use None instead of a number for targets to indicate ALL

			Use generator functions Affect() to get monsters affected and for each damage instance, run it through all participants relevant powers
			after the affect, run through both targets post powers based on the ultimate outcome
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
						Powers = [[POWER.OFFENSE], [POWER.DEFENSE]]
						if affectClass == SOURCE.ATTACK:
							Powers[0].append(POWER.ON_ATTACK)
							Powers[1].append(POWER.VS_ATTACK)
						elif affectClass == SOURCE.SKILL:
							Powers[0].append(POWER.ON_SKILL)
							Powers[1].append(POWER.VS_SKILL)
						elif affectClass == SOURCE.POWER:
							Powers[0].append(POWER.ON_POWER_GAIN)
							Powers[1].append(POWER.VS_POWER_GAIN)
						# First you get to empower your damage
						damage = self.Empower(damage, affectClass, Powers, source=self, target=target)
						# Then the target empowers the damage
						damage = target.Empower(damage, affectClass, Powers, source=self, target=target)
					# Now that damage has been affected and side effects taken care of by powers, deal the damage
					# Anything less than 0 damage is 0 damage
					damage = max(0, damage)
					target_was_alive = target.Alive
					target.Health -= damage
					dealt[-1] += damage
					# Now call post damage powers
					Powers = [[POWER.AFTER_ATTACK],[POWER.AFTER_ATTACK_ED]]
					if damage > 0:
						Powers[0].append(POWER.VS_HP_REDUCE)
						Powers[1].append(POWER.ON_HP_REDUCE)
					if target_was_alive and not target.Alive:
						Powers[0].append(POWER.ON_KILL)
						Powers[1].append(POWER.ON_DEATH)
					self.Empower(damage, affectClass, Powers[0], source=self, target=target)
					target.Empower(damage, affectClass, Powers[1], source=self, target=target)
		# Return damage dealt for logging
		return dealt, targets

"""
#2 MonsterGroup (Instanceable)
	Collective container for one or more Monsters

	ATTRIBUTES:
		* Monsters (list of Monsters)
		* Ephemeral (list of bools to show if Monsters are respawnable or not)
		* fight_on (Number of monsters ready to fight)
	METHODS:
		* AddMonster(Monster)
		* RemoveMonster(Monster) : Some monsters are not removed by dying (ie: DarkSlimes)
		* Reset() : Respawn all non-ephemeral monsters in the group
		* Turn() : This group takes a turn
		* Affect(Monster, OnlySelf, IncludeSelf, All, CheckAlive) : Generator over the group's monsters. If OnlySelf, only yields the Monster if found in the group. IncludeSelf and All work as in the Arena class's Affect(). CheckAlive means the monster needs to respond as alive to be included.
"""
class MonsterGroup():
	def __init__(self, monsters=[], ID="<TemplateGroup>"):
		print(f"Making monster group out of {monsters}")
		self.monsters = monsters
		self.ID = ID
		self.ephemeral = [False for _ in monsters]
		self.fight_on = len(monsters)

	def __str__(self):
		return f"{self.ID}"

	def AddMonster(self, monster, ephemeral=True):
		print(f"Monster Group is adding monster {monster}")
		self.monsters.append(monster)
		self.ephemeral.append(ephemeral)
		self.fight_on += 1

	def RemoveMonster(self, monster):
		monsterIdx = self.monsters.index(monster)
		self.monsters.remove(monster)
		del self.ephemeral[monsterIdx]
		if monster.Alive:
			self.fight_on -= 1

	def Reset(self):
		"""
			Brings back all non-empehermal monsters in the group, garbage collector will kill the others
		"""
		self.monsters = [_ for _, ephemeral in zip(self.monsters, self.ephemeral) if not ephemeral]
		for monster in self.monsters:
			monster.Reset()

	def Turn(self):
		for monster in self.monsters:
			monster.Turn()

	def Affect(self, SourceMonster, OnlySelf=False, IncludeSelf=False, All=False, CheckAlive=True):
		if OnlySelf:
			if SourceMonster in self.monsters:
				yield 1
				yield SourceMonster
		else:
			if IncludeSelf:
				group = [_ for _ in self.monsters if _.Alive]
			else:
				group = [_ for _ in self.monsters if _.Alive and _ != SourceMonster]
			yield len(group)
			for monster in group:
				yield monster

"""
#3 Arena (Instanceable)
	The Arena holds MonsterGroups to fight one another. MonsterGroups get to fight in the order they are added
	ATTRIBUTES:
		* Groups (list of MonsterGroups)
		* Turn (integer)
	METHODS:
		* AddGroup(MonsterGroup) : Add a group of monsters to the fight
		* RemoveGroup(MonsterGroup) : Remove a group of monsters from the fight
		* Reset() : Respawn all monsters in all groups
		* Turn() : Execute a turn of combat
		* Affect(MonsterGroup, IncludeSelf, All) : Generator for included MonsterGroups. Only includes the self-group if IncludeSelf is True, only affects one group at random unless All is True
"""
class Arena():
	def __init__(self, groups=[], ID="<TemplateArena>"):
		self.groups = groups
		self.turn = 0
		self.ID = ID
		global global_rng
		self.rng = global_rng

	def __str__(self):
		return self.ID

	def AddGroup(self, group):
		self.groups.append(group)

	def RemoveGroup(self, group):
		self.groups.remove(group)

	def Reset(self):
		for group in self.groups:
			group.Reset()

	def Turn(self):
		for group in self.groups:
			group.Turn()

	def Affect(self, Friendly, IncludeSelf=False, All=False):
		if not IncludeSelf:
			groups = [_ for _ in self.groups if _ != Friendly]
		else:
			groups = dcpy(self.groups)
		if not All:
			# Trim to one group
			groups = self.rng.choices(groups, k=1)
		# Iterate over all affected groups
		yield len(groups)
		for group in groups:
			yield group

	def Brawl(self):
		self.Reset()
		fight_on = sum([bool(group.fight_on) for group in self.groups])
		while fight_on >= 2:
			self.Turn()
			fight_on = sum([bool(group.fight_on) for group in self.groups])
		winner = None
		for group in self.groups:
			if group.fight_on:
				winner = group
				break
		return winner

