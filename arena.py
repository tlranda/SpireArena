# Slay the Spire Arena: Pit mobs vs one another and fight it out to the death!
import random
global_rng = random.Random()
from copy import deepcopy as dcpy
# Defines power API
from powers import *
from monsters import *

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

	def __iter__(self):
		for monster in self.monsters:
			yield monster

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
		# Tick all powers for all monsters after the group's turn
		for monster in self.monsters:
			removePowers = []
			for power in monster.PowerPool:
				remove = power.TurnTick()
				if remove:
					removePowers.append(power)
			# Remove expired powers
			for power in removePowers:
				monster.PowerPool.remove(power)

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

	def __iter__(self):
		for group in self.groups:
			yield group

	def AddGroups(self, *groups):
		self.groups.extend(groups)

	def RemoveGroups(self, *groups):
		for group in groups:
			self.groups.remove(group)

	def Reset(self):
		self.turn = 0
		for group in self.groups:
			group.Reset()

	def Turn(self):
		print(f"ARENA BEGINS TURN {self.turn}")
		for group in self.groups:
			group.Turn()
		self.turn += 1

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

	def Brawl(self, max_turns = None):
		self.Reset()
		fight_on = sum([bool(group.fight_on) for group in self.groups])
		while fight_on >= 2:
			if max_turns is not None and self.turn >= max_turns:
				print(f"ARENA TURN LIMIT REACHED")
				break
			self.Turn()
			fight_on = sum([bool(group.fight_on) for group in self.groups])
		winners = []
		for group in self.groups:
			if group.fight_on:
				winners.append(group)
		return winners

