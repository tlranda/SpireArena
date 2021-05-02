# Slay the Spire Arena: Pit mobs vs one another and fight it out to the death!
import random
# This is the ONLY rng source that should be used in Arena code--implementers can use their own RNG separately
global_rng = random.Random()
from copy import deepcopy as dcpy
# Globally controls debug output and perhaps other things in the future
import settings

"""
#2 MonsterGroup (Instanceable)
	Collective container for one or more Monsters

	ATTRIBUTES/PROPERTIES:
		* monsters (list of Monsters)
		* ephemeral (list of bools to show if Monsters are respawnable or not)
		* fight_on (Number of monsters ready to fight)
		* GroupStatus : True if group can keep fighting, else False
	METHODS:
		* AddMonsters(*Monsters)
		* RemoveMonsters(*Monsters) : Explicitly remove monsters from a group
		* Reset() : Respawn all non-ephemeral monsters in the group
		* Turn() : This group takes a turn
		* Affect(Monster, OnlySelf, IncludeSelf, All, CheckAlive) : Generator over the group's monsters.
				If OnlySelf, only yields the Monster if found in the group.
				IncludeSelf and All work as in the Arena class's Affect().
				CheckAlive means the monster needs to respond as alive to be included.
		* MoveGroup(Arena) : Move group and all monsters in it to a new arena
"""
class MonsterGroup():
	# monsters = list of preset monsters (assumed non-ephemeral)
	# ID = string name for group
	def __init__(self, monsters=None, setting=None, ID="<TemplateGroup>"):
		if monsters is None:
			monsters = list()
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"Making{' empty' if monsters == [] else ''} monster group {ID}{' out of '+','.join([str(m) for m in monsters]) if monsters != [] else ''}")
		self.ID = ID
		self.setting = setting
		self.monsters = []
		self.ephemeral = []
		for monster in monsters:
			# Ensure monster is aware of its surroundings
			monster.ChangeEnvironment(battlefield=self.setting, friendly=self)
			# Track data for the group
			self.ephemeral.append(False)
			self.monsters.append(monster)
		self.fight_on = len(monsters)

	def __str__(self):
		if self.monsters == []:
			return f"{self.ID} -- EMPTY MonsterGroup"
		monsterStatuses = []
		for monster, ephStatus in zip(self.monsters, self.ephemeral):
			monsterStatuses.append(f"{str(monster)}->[{'alive' if monster.Alive else 'dead'}{', (Ephemeral)' if ephStatus else ''}]")
		return f"{self.ID} contains {', '.join(monsterStatuses)}"

	def __iter__(self):
		for monster in self.monsters:
			yield monster

	# Boolean for whether the group is eligible for combat
	@property
	def GroupStatus(self):
		return self.fight_on > 0

	# Add monsters to the group, assumed to be ephemeral (not resurrected when group is reset) unless otherwise specified
	def AddMonsters(self, ephemeral=True, *monsters):
		for monster in monsters:
			if settings.DEBUG.full == settings.ARENA_DEBUG:
				print(f"{str(self)} adds monster {monster}")
			# Ensure monster is aware of its surroundings, which includes this friendly group and this arena
			monster.ChangeEnvironment(battlefield=self.setting, friendly=self)
			# Track data for the group
			self.monsters.append(monster)
			self.ephemeral.append(ephemeral)
			self.fight_on += 1

	# Remove monsters from the group, dissassociating them from the group but not the Arena
	def RemoveMonsters(self, *monsters):
		for monster in monsters:
			try:
				monsterIdx = self.monsters.index(monster)
			except IndexError:
				# Cannot remove a monster that is not in this group
				pass
			else:
				if settings.DEBUG.full == settings.ARENA_DEBUG:
					print(f"{str(self)} removes monster {monster}")
				self.monsters.remove(monster)
				# Delink monster affiliation with THIS GROUP, but it may remain in the arena until otherwise specified
				monster.ChangeEnvironment(friendly=None)
				del self.ephemeral[monsterIdx]
				if monster.Alive:
					self.fight_on -= 1

	# Bring back non-ephemeral monsters
	def Reset(self):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{str(self)} is resetting.")
		new_monsters, new_ephemeral = [], []
		for idx, truth in enumerate(self.ephemeral):
			if not truth:
				new_monsters.append(self.monsters[idx])
				new_ephemeral.append(False)
				if settings.DEBUG.full == settings.ARENA_DEBUG:
					print("\t"+f"Non-ephemeral monster {new_monsters[-1]} is reset")
				new_monsters[-1].Reset()
			elif settings.DEBUG.full == settings.ARENA_DEBUG:
				print("\t"+f"Ephemeral monster {self.monsters[idx]} will not be reset and exits the group")
		self.monsters = new_monsters
		self.ephemeral = new_ephemeral
		self.fight_on = len(self.monsters)

	# All monsters in the group are given a turn
	def Turn(self):
		if settings.ARENA_DEBUG == settings.DEBUG.full:
			print(f"{self.ID} takes turns for all monsters in its group")
		for monster in self.monsters:
			monster.Turn()
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{self.ID} ticks all powers in its group")
		# Tick all powers for all monsters after the group's turn
		for monster in self.monsters:
			removePowers = []
			for power in monster.PowerPool:
				if power.TurnTick(): # True when tick results in power expiring
					removePowers.append(power)
			# Remove expired powers
			for power in removePowers:
				monster.PowerPool.remove(power)

	# Condition-based generator to look up monsters in the group
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

	# Call to move group and all of its monsters to a new arena
	def MoveGroup(self, newSetting):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{self.ID} moves from "+\
				f"{self.setting.ID if self.setting is not None else 'None'} to "+\
				f"{newSetting.ID if newSetting is not None else 'None'}")
		self.setting = newSetting
		for monster in self.monsters:
			monster.ChangeEnvironment(battlefield=newSetting)

"""
#3 Arena (Instanceable)
	The Arena holds MonsterGroups to fight one another. MonsterGroups get to fight in the order they are added
	ATTRIBUTES:
		* groups (list of MonsterGroups)
		* turn (integer)
		* ID (string)
		* rng (randomization)
	METHODS:
		* AddGroups(*MonsterGroups) : Add some # of groups of monsters to the fight
		* RemoveGroups(*MonsterGroup) : Remove some # of groups of monsters from the fight
		* Reset() : Respawn all monsters in all groups
		* Turn() : Execute a turn of combat
		* Affect(MonsterGroup, OnlySelf, IncludeSelf, All) : Generator for included MonsterGroups.
				Only includes the self-group if IncludeSelf is True, only affects one group at random unless All is True
		* Brawl(turn_limit=None) : Fight all groups to the death or turn limit, returns surviving groups
"""
class Arena():
	def __init__(self, groups=None, ID="<TemplateArena>"):
		if groups is None:
			groups = list()
		self.ID = ID
		self.turn = 0
		global global_rng
		self.rng = global_rng
		self.groups = []
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"Creating{' empty' if groups == [] else ''} arena {ID}{' with Groups '+', '.join([str(g) for g in groups]) if groups != [] else ''}")
		for group in groups:
			group.MoveGroup(self)
			self.groups.append(group)

	def __str__(self):
		if self.groups == []:
			return f"{self.ID} -- EMPTY Arena"
		return f"{self.ID} contains "+\
			f"{', '.join([group.ID+':'+('alive' if group.GroupStatus else 'eliminated') for group in self.groups])}"

	def __iter__(self):
		for group in self.groups:
			yield group

	def AddGroups(self, *groups):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{self.ID} adds Groups: {', '.join([g.ID for g in groups])}")
		for group in groups:
			group.MoveGroup(self)
			self.groups.append(group)

	def RemoveGroups(self, *groups):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{self.ID} adds Groups: {', '.join([g.ID for g in groups])}")
		for group in groups:
			try:
				self.groups.remove(group)
			except IndexError:
				# Attempted to remove a group that this arena is NOT responsible for
				pass
			else:
				group.MoveGroup(None)

	def Reset(self):
		if settings.DEBUG.full == settings.ARENA_DEBUG:
			print(f"{self.ID} resets")
		self.turn = 0
		for group in self.groups:
			group.Reset()

	def Turn(self):
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{self.ID} BEGINS TURN {self.turn}")
		for group in self.groups:
			group.Turn()
		self.turn += 1

	def Affect(self, Friendlies, OnlySelf=False, IncludeSelf=False, All=False):
		if OnlySelf:
			groups = [_ for _ in self.groups if _ == Friendlies]
		elif not IncludeSelf:
			groups = [_ for _ in self.groups if _ != Friendlies]
		else:
			groups = dcpy(self.groups)
		if not All:
			# Trim to one group
			groups = self.rng.choices(groups, k=1)
		# Iterate over all affected groups
		yield len(groups)
		for group in groups:
			yield group

	def Brawl(self, max_turns=None):
		self.Reset()
		fight_on = sum([int(group.GroupStatus) for group in self.groups])
		while fight_on >= 2:
			if max_turns is not None and self.turn >= max_turns:
				if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
					print(f"{self.ID} TURN LIMIT REACHED")
				break
			self.Turn()
			fight_on = sum([int(group.GroupStatus) for group in self.groups])
		winners = []
		for group in self.groups:
			if group.fight_on:
				winners.append(group)
		return winners

