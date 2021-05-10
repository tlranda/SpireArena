# Should not need more than these enums and the makePower call
from powers import SOURCE, TRIGGER, makePower, affectLookup
from arena import MonsterGroup
import settings

"""
	TODO:
		Make Monster.Alive a property or lambda or something?
		Make monsters have a GainBlock() function similar to damage (can grant block to others too a la Shield Gremlin)
			Make sure the block from GainBlock reduces HP damage and triggers proper power triggers etc etc etc
"""

"""
#0 MonsterMove (Abstract)
	Defines a particular monster move
	Given a class, energy cost, callback, and string-able attributes
"""
class MonsterMove():
	def __init__(self, affectClass, callback, isStatus=False, description="<No move description provided>", energyCost='X'):
		self.affectClass = affectClass
		self.callback = callback
		self.cost = energyCost
		self.isStatus = isStatus
		self.ID = callback.__name__
		self.description = description

	def __str__(self):
		return f"{self.ID} defined as {self.description}"

	def call(self, monster):
		"""
			Spend the required energy if available, then make the callback
			Entanglement check alongside cost?
		"""
		if (self.cost == 'X' and monster.Energy > 0) or (monster.Energy >= self.cost):
			paid = self.cost if type(self.cost) is int else monster.Energy
			monster.Energy -= paid
			self.callback(paid)
			# Play and class triggers occur
			monster.Empower(None, SOURCE.FX, *affectLookup[self.affectClass], source=monster, target=None, extras=None)
		elif settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{str(monster)} has insufficient energy {monster.Energy} to cast {self.ID} (costs {self.cost})")

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
				* Act (int)
				* BaseDraw (int)
				* BaseEnergy, Energy (int, int)
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
		self.rng = settings.global_rng
		self.Name, self.Act, self.ascension = "<GenericMonster>", 0, 0
		self.MaxHealth, self.Health, self.Block, self.BaseDraw, self.BaseEnergy, self.Energy = 0, 0, 0, 5, 2, 0
		self.HistoryLimit, self.Pattern, self.Abilities, self.Callbacks = 0, [], [], []
		self.PowerPool = [makePower('block'), makePower('blockLossEachTurn'), makePower('die')]
		self.History, self.HistoryIdx = [], 0
		self.Alive = True # Should become a property

	def Reset(self):
		self.Health = self.MaxHealth
		if not self.Alive and self.Friendlies is not None:
			self.Friendlies.fight_on += 1
		self.BaseDraw = self.BaseDraw
		self.BaseEnergy = 2+self.Act
		self.Alive = True
		self.PowerPool = [makePower('block'), makePower('blockLossEachTurn'), makePower('die')]
		self.History = []
		self.HistoryIdx = 0

	def __str__(self):
		string = f"{self.Name} {self.ID} [{self.Health}/{self.MaxHealth} HP]"
		if self.Friendlies is not None:
			string = f"{self.Friendlies.ID}::{string}"
		if self.Arena is not None:
			string = f"{self.Arena.ID}::{string}"
		return string

	"""
		SOMEWHAT DISGUSTING PYTHON BUT HERE'S HOW IT WORKS
		Actual signature = ChangeEnvironment(self, battlefield, friendly)
			BUT the arguments aren't required and ONLY the provided ones are used.
		This means that not passing an argument DOES NOT change that value to None,
		but passing None as an argument DOES change the value to None

		If you are reading the source and know a better way to achieve this,
		feel free to submit a pull request
	"""
	def ChangeEnvironment(self, **kwargs):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{str(self)} edits environment to reflect new status given by {', '.join([str(k)+':'+str(v) for k,v in zip(kwargs.keys(), kwargs.values())])}")
		if 'battlefield' in kwargs.keys():
			self.Arena = kwargs['battlefield']
		if 'friendly' in kwargs.keys():
			self.Friendlies = kwargs['friendly']

	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		"""
			No special intents by default
		"""
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{self.Name}'s move is not overridden by template class's SpecialIntent()")
		return moveCall

	def SpecialMoveSet(self, *moveChances):
		"""
			No special moves by default, should be list of tuples of (move, chance)
			Should redefine ALL moves else they will be disabled.
			Probabilities will be weighted for the sum to equal 1 even if the given ones don't
		"""
		if len(moveChances) == 0 and settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{self.Name}'s chances are not overridden by template class's SpecialMoveSet()")
		else:
			weight = [0 for _ in self.Pattern]
			for tup in moveChances:
				move, chance = tup
				idx = self.Callbacks.index(move)
				weight[idx] = chance
			wsum = sum(weight)
			if wsum != 1.:
				weight = [w / wsum for w in weight]
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print(f"{str(self)} adjusts move probabilities from {self.Pattern} to {weight}")
			self.Pattern = weight

	def makeMoves(self, *move_tuples):
		n_moves = len(move_tuples)
		self.Callbacks = []
		self.Abilities = []
		self.Pattern = [1/n_moves for _ in range(n_moves)]
		self.HistoryLimit = n_moves
		for move in move_tuples:
			# Source, [Callback], isStatus, Description
			self.Callbacks.append(move[1])
			self.Abilities.append(MonsterMove(*move))

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
		if len(self.History) < 2 and move_idx < self.HistoryLimit:
			self.History.append(move_idx)
		elif move_idx < self.HistoryLimit:
			self.History[self.HistoryIdx] = move_idx
		self.HistoryIdx = (self.HistoryIdx + 1) % 2
		return move

	def Turn(self, move=None, solo_action=False):
		"""
			Monster takes its turn
			NOTE: TURN_START and TURN_END triggers are AUTOMATICALLY called by MonsterGroup for collective triggering semantics
			ONLY set solo_action=True if you know what you are doing
		"""
		if self.Alive:
			if solo_action:
				self.Empower(None, SOURCE.FX, TRIGGER.TURN_START, source=self, target=None, extras=None)
			self.Energy = self.BaseEnergy
			# Card draw implementation
			isStatus = True
			while isStatus and self.Energy > 0: # Add hand played term when playing cards is added, as you could have 1 energy and all 2-costs or something
				# Move through statuses then select a move
				move = self.MoveSelect(move)
				move.call(self)
			if solo_action:
				self.Empower(None, SOURCE.FX, TRIGGER.TURN_END, source=self, target=None, extras=None)
		elif settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{str(self)} is dead. Skipping move portion of turn")

	def Empower(self, value, source_class, *trigger_classes, source, target, extras=None):
		"""
			Alter value using self.PowerPool based on trigger_class and source_class
		"""
		if extras is None:
			extras = list()
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
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print("\t"+f"{str(self)} triggers power {power}")
			new_value = power.Affect(value, source_class, source, target, extras)
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print("\t"+f"{str(self)}'s {power} updates value from {value} to {new_value}")
			value = new_value
		return value

	def Select(self, ArenaTargets=1, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True):
		"""
			Use generator functions Affect() to get monsters affected and for each damage instance, run it through all participants relevant powers
			after the affect, run through both targets post powers based on the ultimate outcome
		"""
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			nlt="\n\t"
			print(f"Select args:{nlt}{nlt.join([key+':'+str(arg) for key,arg in zip(['ArenaTargets', 'ArenaOnlySelf', 'ArenaIncludeSelf', 'ArenaAll', 'GroupTargets', 'GroupOnlySelf', 'GroupIncludeSelf', 'GroupAll', 'GroupCheckAlive'],[ArenaTargets, ArenaOnlySelf, ArenaIncludeSelf, ArenaAll, GroupTargets, GroupOnlySelf, GroupIncludeSelf, GroupAll, GroupCheckAlive])])}")
		# Get all the candidate groups
		arenaGroups = [val for val in self.Arena.Affect(self.Friendlies, OnlySelf=ArenaOnlySelf, IncludeSelf=ArenaIncludeSelf, All=ArenaAll, Count=ArenaTargets)]
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"Select Candidate Groups = {' | '.join([', '.join([str(g) for g in ag]) for ag in arenaGroups[1:]])}")
		if arenaGroups[0] == 0:
			# There are no valid targets, return None
			return None

		# Now select group targets in each group
		monsterGroups = [[val for val in group.Affect(self, GroupOnlySelf, GroupIncludeSelf, GroupAll, GroupCheckAlive, Count=GroupTargets)] for group in arenaGroups[1:]]
		available_monsters = sum([group[0] for group in monsterGroups])
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"Select From {available_monsters} Candidate Monsters = {' | '.join([','.join([str(g) for g in mg[1:]]) for mg in monsterGroups])}")
		if available_monsters == 0:
			# There are no valid targets, return None
			return None
		# Make actual targets
		targetedMonsters = []
		for monsterList in monsterGroups:
			targetedMonsters.extend(monsterList[1:])
		if GroupTargets is not None:
			# Randomly target monsters across groups up to the number of targets
			targetedMonsters = self.rng.sample(targetedMonsters, k=min(len(targetedMonsters), GroupTargets))
		# Return the targeted Monsters
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"Target {len(targetedMonsters)} = {' | '.join([str(m) for m in targetedMonsters])}")
		return targetedMonsters

	def ApplyPowers(self, *powers, affectClass=SOURCE.SKILL,
				ArenaTargets=1, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
				extras=None):
		"""
			CALL FROM THE OBJECT APPLYING THE POWERS
			powers = list of Power objects to add to the target Objects
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if this application triggers any other powers
			others specify how to locate targets for the power application
		"""
		if extras is None:
			extras = list()
		targets = self.Select(ArenaTargets=ArenaTargets, ArenaOnlySelf=ArenaOnlySelf, ArenaIncludeSelf=ArenaIncludeSelf, ArenaAll=ArenaAll,
				GroupTargets=GroupTargets, GroupOnlySelf=GroupOnlySelf, GroupIncludeSelf=GroupIncludeSelf, GroupAll=GroupAll, GroupCheckAlive=GroupCheckAlive)
		if targets is None:
			# The move fails due to no targets
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print(f"Power instance {[str(p) for p in powers]} fails to apply -- NO VALID TARGETS")
			return [None]
		enemies = self.Select(ArenaTargets=1, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=True,
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
				targets_enemies = target.Select(ArenaTargets=1, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=True,
								GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=GroupCheckAlive)
				for target_enemy in targets_enemies:
					# Allies of the target and the target itself don't get VS triggers
					target_enemy.Empower(powers, affectClass, *Powers[1], source=self, target=target, extras=extras)
		# Return targets for logging
		return targets

	def GainBlock(self, *amounts, empowerBlock=True, affectClass=SOURCE.SKILL,
				ArenaTargets=1, ArenaOnlySelf=True, ArenaIncludeSelf=True, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=True, GroupIncludeSelf=True, GroupAll=False, GroupCheckAlive=True,
				extras=None):
		"""
			CALL FROM THE OBJECT APPLYING THE BLOCK
			amounts = list of raw block values to produce (affected by powers)
			empowerBLock determines if powers apply to the block gain (either both ways or no ways)
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if powers interact differently
			others specify how to locate targets for the damage instance
		"""
		if extras is None:
			extras = list()
		targets = self.Select(ArenaTargets=ArenaTargets, ArenaOnlySelf=ArenaOnlySelf, ArenaIncludeSelf=ArenaIncludeSelf, ArenaAll=ArenaAll,
				GroupTargets=GroupTargets, GroupOnlySelf=GroupOnlySelf, GroupIncludeSelf=GroupIncludeSelf, GroupAll=GroupAll, GroupCheckAlive=GroupCheckAlive)
		if targets is None:
			# The move fails due to no targets
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print(f"Block instance {amounts} fails to trigger -- NO VALID TARGETS")
			return [0], [None]
		applied = []
		# Iteratively gain block
		for block in amounts:
			if self.Alive:
				for target in targets:
					applied.append(0)
					if empowerBlock:
						Powers = [[TRIGGER.DEFENSE], [TRIGGER.DEFENSE]]
						if affectClass == SOURCE.ATTACK:
							Powers[0].append(TRIGGER.ON_ATTACK)
							#Powers[1].append(TRIGGER.VS_ATTACK)
						if affectClass == SOURCE.SKILL:
							Powers[0].append(TRIGGER.ON_SKILL)
							Powers[1].append(TRIGGER.VS_SKILL)
						elif affectClass == SOURCE.TRIGGER:
							Powers[0].append(TRIGGER.ON_POWER_GAIN)
							Powers[1].append(TRIGGER.VS_POWER_GAIN)
						# First you get to empower your block
						block = self.Empower(block, affectClass, *Powers[0], source=self, target=target, extras=extras)
						# Then the target empowers the block
						block = target.Empower(block, affectClass, *Powers[1], source=self, target=target, extras=extras)
					# Now that block has been affected and side effects taken care of by powers, apply the block
					# Anything less than 0 block is 0 block
					block = max(0, block)
					target.Block += block
					applied[-1] += block
					# There should not be post-block powers to apply
		# Return block applied for logging
		return applied, targets

	def Damage(self, *amounts, empowerDamage=True, affectClass=SOURCE.ATTACK,
				ArenaTargets=1, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
				GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
				extras=None):
		"""
			CALL FROM THE OBJECT DEALING THE DAMAGES
			amounts = list of damage values to produce (affected by powers)
			empowerDamage determines if powers apply to the damage instance (either both ways or no ways)
			affectClass is enum for ATTACK/POWER/SKILL/FX to determine if powers interact differently
			others specify how to locate targets for the damage instance
		"""
		if extras is None:
			extras = list()
		targets = self.Select(ArenaTargets=ArenaTargets, ArenaOnlySelf=ArenaOnlySelf, ArenaIncludeSelf=ArenaIncludeSelf, ArenaAll=ArenaAll,
				GroupTargets=GroupTargets, GroupOnlySelf=GroupOnlySelf, GroupIncludeSelf=GroupIncludeSelf, GroupAll=GroupAll, GroupCheckAlive=GroupCheckAlive)
		if targets is None:
			# The move fails due to no targets
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print(f"Damage instance {amounts} fails to trigger -- NO VALID TARGETS")
			return [0], [None]
		# Iteratively perform damage
		dealt = []
		for damage in amounts:
			# Can stop multiattacks early etc if die during the effect
			if self.Alive:
				for target in targets:
					dealt.append(0)
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
					Powers = [[],[]]
					if damage > 0:
						Powers[0].append(TRIGGER.VS_HP_REDUCE)
						Powers[1].append(TRIGGER.ON_HP_REDUCE)
					if target_was_alive and not target.Alive:
						Powers[0].append(TRIGGER.ON_KILL)
						Powers[1].append(TRIGGER.ON_DEATH)
					if len(Powers[0]) > 0:
						self.Empower(damage, affectClass, *Powers[0], source=self, target=target, extras=extras)
					if len(Powers[1]) > 0:
						target.Empower(damage, affectClass, *Powers[1], source=self, target=target, extras=extras)
		# Return damage dealt for logging
		return dealt, targets

# Routine to contruct monsters based on one-line, space-delimited strings
def makeMonsterFromString(string, battlefield=None, monsterGroup=None):
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
def makeMonsterGroupFromFile(fh, battlefield=None, ID=None):
	if ID is None:
		global num_groups
		ID = f"Group_{num_groups}"
		num_groups += 1
	monsterGroup = MonsterGroup(ID=ID)
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
		monsterGroup.AddMonsters(False, makeMonsterFromString(line, battlefield, monsterGroup))
	if battlefield is not None:
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
def makeMonster(MonsterType, **kwargs):
	return objects[MonsterType](**kwargs)

