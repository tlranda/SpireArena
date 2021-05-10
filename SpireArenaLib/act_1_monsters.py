import powers, monsters, settings

def objects():
	return {"AcidSlime": AcidSlime,
	       	"Slaver": Slaver,
	        "JawWorm": JawWorm,
	        "Cultist": Cultist,
	        "Louse": Louse}

class AcidSlime(monsters.Monster):
	'''
		Known parties:
			* Acid Slime L
			* Acid Slime M, Spike Slime S
			* Acid Slime M, Slaver
			* Acid Slime M, Cultist
			* Acid Slime M, Looter
			* Acid Slime M, Jaw Worm
			* Acid Slime M, Fungi Beast
			* Acid Slime S, Spike Slime S, Spike Slime S, Spike Slime S, Acid Slime S
			* Acid Slime S, Spike Slime M
	'''
	def __init__(self, ID="<TemplateAcidSlime>", Arena=None, Friendlies=None, ascension=0, variant=0):
		# Ensure proper type
		ascension, variant = int(ascension), int(variant)
		# Constructor
		super().__init__(ID, Arena, Friendlies)
		self.Size = ['L', 'M', 'S'][variant]
		self.Name = f"Acid Slime ({self.Size})"
		self.Act = 1
		# Stats
		if self.Size == 'L':
			self.MaxHealth = self.rng.randint(65,69)
			self.AscendMaxHealth = 3
		elif self.Size == 'M':
			self.MaxHealth = self.rng.randint(28,32)
			self.AscendMaxHealth = self.rng.randint(1,2)
		else: # self.Size == 'S':
			self.MaxHealth = self.rng.randint(8,12)
			self.AscendMaxHealth = 1
		# Moves
		self.makeMoves((powers.SOURCE.ATTACK, self.Corrosive_Spit, False, f"{str(self)} spits"),
						(powers.SOURCE.ATTACK, self.Tackle, False, f"{str(self)} tackles"),
						(powers.SOURCE.SKILL, self.Lick, False, f"{str(self)} licks"))
		if self.Size == 'S':
			self.SpecialMoveSet((self.Tackle, 0.5),
								(self.Lick, 0.5))
		else:
			self.SpecialMoveSet((self.Corrosive_Spit, 0.3),
								(self.Tackle, 0.4),
								(self.Lick, 0.3))
		# Powers
		# self.PowerPool = [Power(SPLIT) # at/below half HP splits into 2 Acid Slime (M) with current HP]
		# Ascend the mortal form
		self.ascension = ascension
		if ascension > 0:
			self.Ascend(ascension)
		# Call Reset to propagate everything properly
		self.Reset()

	def Ascend(self, ascension):
		if self.ascension < 7 and ascension >= 7:
			self.MaxHealth += self.AscendMaxHealth
			self.SpecialMoveSet((self.Corrosive_Spit, 0.4),
								(self.Tackle, 0.3),
								(self.Lick, 0.3))
		elif self.ascension >= 7 and ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
			self.SpecialMoveSet((self.Corrosive_Spit, 0.3),
								(self.Tackle, 0.4),
								(self.Lick, 0.3))

	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		# Slime cannot use Tackle twice in a row
		if self.Size == 'L' or (self.Size == 'M' and self.ascension < 17):
			ForbiddenIdx = self.Callbacks.index(self.Tackle)
		elif self.Size == 'M' and self.ascension >= 17:
			ForbiddenIdx = self.Callbacks.index(self.Lick)
		elif self.Size == 'S':
			if self.ascension >= 17 and len(self.History) == 0:
				# Has to start on lick
				moveIdx = self.Callbacks.index(self.Lick)
				moveCall = self.Abilities[moveIdx]
			elif self.ascension >= 2 and len(self.History) > 0:
				# Alternates between Lick and Tackle moves
				prevCall = moveCall
				lickCall = self.Abilities[self.Callbacks.index(self.Lick)]
				tackleCall = self.Abilities[self.Callbacks.index(self.Tackle)]
				moveCall = lickCall if self.History[(self.HistoryIdx-1)%2] == self.Callbacks.index(self.Tackle) else tackleCall
			return moveCall
		if moveCall == self.Abilities[ForbiddenIdx]:
			if len(self.History) >= 1 and self.History[(self.HistoryIdx-1)%2] == ForbiddenIdx:
				moveCall = self.rng.choices(moveAlternatives, moveChances, k=1)[0]
		return moveCall

	def Corrosive_Spit(self, paid):
		if self.Size == 'L':
			n_slimed = 2
			if self.ascension >= 2:
				damage = 12
			else:
				damage = 11
		elif self.Size == 'M':
			n_slimed = 1
			if self.ascension >= 2:
				damage = 8
			else:
				damage = 7
		# Deal damage
		# Shuffle n_slimed slime statuses into target's discard pile (however that is implemented)
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses CORROSIVE_SPIT to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to {[str(monster) for monster in targets]} and shuffle {n_slimed} into {[str(monster) for monster in targets]}'s discard!!")

	def Lick(self, paid):
		if self.Size == 'L':
			weak = 2
		else: # self.Size == 'M' or 'S':
			weak = 1
		# Apply weak to targets
		targets = self.ApplyPowers(powers.makeWeak(weak), affectClass=self.Abilities[self.Callbacks.index(self.Lick)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=True,
						extras=[])
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses LICK to apply {weak} weak to {[str(monster) for monster in targets]}!!")

	def Tackle(self, paid):
		if self.Size == 'L':
			if self.ascension >= 2:
				damage = 18
			else:
				damage = 16
		elif self.Size == 'M':
			if self.ascension >= 2:
				damage = 12
			else:
				damage = 10
		else: # self.Size = 'S'
			if self.ascension >= 2:
				damage = 4
			else:
				damage = 3
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses TACKLE to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to {[str(monster) for monster in targets]}!!")


# work in progress

class Slaver(monsters.Monster):
	'''
	Known Parties:
		Act 1:
			Blue Slaver
			Blue Slaver, Louse
			Blue Slaver, Acid Slime (M)
			Blue Slaver, Spike Slime (M)
			Red Slaver
			Red Slaver, Louse
			Red Slaver, Acid Slime (M)
			Red Slaver, Spike Slime (M)
		Act 2:
			Blue Slaver, Red Slaver, TaskMaster
	'''
	def __init__(self, ID="<TemplateSlaver>", Arena=None, Friendlies=None, ascension=0, variant=0):
		# Ensure proper type
		ascension, variant = int(ascension), int(variant)
		# Constructor
		super().__init__(ID, Arena, Friendlies)
		self.Color = ['Blue', 'Red'][variant]
		self.Name = f"{self.Color} Slaver"
		self.Act = 1
		# Stats
		self.MaxHealth = self.rng.randint(46,50)
		self.AscendMaxHealth = 2
		# Moves
		self.makeMoves((powers.SOURCE.ATTACK, self.Stab, False, f"{str(self)} stabs"),
						(powers.SOURCE.ATTACK, self.Rake, False, f"{str(self)} rakes"),
						(powers.SOURCE.ATTACK, self.Scrape, False, f"{str(self)} scrapes"),
						(powers.SOURCE.SKILL, self.Entangle, False, f"{str(self)} throws net"))
		if self.Color == 'Blue':
			self.SpecialMoveSet((self.Stab, 0.4),
								(self.Rake, 0.6))
		else:
			"""
				Actually forced to STAB first turn
				Then SCRAPE, SCRAPE, STAB explicitly until 25% chance ENTANGLE triggers
				Then 45% STAB 55% SCRAPE post-ENTANGLE
			"""
			self.SpecialMoveSet((self.Stab, 0.3375),
								(self.Scrape, 0.4125),
								(self.Entangle, 0.25))
		# Powers
		# self.PowerPool.Append(Power(Entangle)) # stops target from attacking for one turn]
		# Ascend the mortal form
		self.ascension = ascension
		if ascension > 0:
			self.Ascend(ascension)
		# Call Reset to propagate everything properly
		self.Reset()

	def Ascend(self, ascension):
		if self.ascension < 7 and ascension >= 7:
			self.MaxHealth += self.AscendMaxHealth
		elif self.ascension >= 7 and ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
	'''
	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		TBD
	'''

	def Stab(self, paid):
		if self.Color == 'Blue':
			if self.ascension >= 2:
				damage = 13
			else:
				damage = 12
		elif self.Color == 'Red':
			if self.ascension >= 2:
				damage = 14
			else:
				damage = 13
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Stab to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to {[str(monster) for monster in targets]}!!")

	def Rake(self, paid):
		#just for Blue Slaver applys weak and does damage to single target
		if self.ascension >= 2:
			damage = 8
		else:
			damage = 7
		if self.ascension >= 17:
			weak = 2
		else:
			weak = 1

		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		# Apply weak to target
		targets = self.ApplyPowers(powers.makeWeak(weak), affectClass=self.Abilities[self.Callbacks.index(self.Rake)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=True,
						extras=[])
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Rake to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage and apply {weak} weak to {[str(monster) for monster in targets]}!!")

	def Scrape(self, paid):
		# ONLY RED SLAVER CAN USE Scrape
		if self.ascension >= 2:
			damage = 9
		else:
			damage = 8
		if self.ascension >= 17:
			vulnerable = 2
		else:
			vulnerable = 1
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		#Applies Vulnerable
		vulnerablePower = powers.Power(timings=powers.TRIGGER.DEFENSE, priority=3, turns=vulnerable, callback=powers.VULNERABLE, AffectDescription=powers.DESCRIPTIONS.VULNERABLE)
		targets = self.ApplyPowers(vulnerablePower, affectClass=self.Abilities[self.Callbacks.index(self.Scrape)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=True,
						extras=[])
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Scrape to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage and apply {vulnerable} vulnerable to {[str(monster) for monster in targets]}!!")

	def Entangle(self, paid):
		# ONLY RED SLAVER CAN USE Entangle
		# Entangle stops target from using attack next turn
		entangle = 1
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Entangle to apply 1 entangle!")

'''
work in progress
needs strength power
needs act based varients
'''
class JawWorm(monsters.Monster):
	'''
		Known Parties:
		Act 1:
			Jaw Worm
			Jaw Worm, Louse
			Jaw Worm, Acid Slime (M)
			Jaw Worm, Spike Slime (M)
		Act 3:
			Jaw Worm *3
	'''
	def __init__(self, ID="<TemplateJawWorm>", Arena=None, Friendlies=None, ascension=0, act=0):
		# Ensure proper type
		ascension, act = int(ascension), int(act)
		# Constructor
		super().__init__(ID, Arena, Friendlies)
		self.Name = f"Jaw Worm"
		self.Act = act
		# Stats
		self.MaxHealth = self.rng.randint(40,44)
		self.AscendMaxHealth = 2

		# Moves
		self.makeMoves((powers.SOURCE.ATTACK, self.Chomp, False, f"{str(self)} chomps"),
						(powers.SOURCE.ATTACK, self.Thrash, False, f"{str(self)} thrashs"),
						(powers.SOURCE.POWER, self.Bellow, False, f"{str(self)} bellows"))
		self.SpecialMoveSet((self.Chomp, 0.25),
							(self.Thrash, 0.3),
							(self.Bellow, 0.45))

		# Ascend the mortal form
		self.ascension = ascension
		if ascension > 0:
			self.Ascend(ascension)
		# Call Reset to propagate everything properly
		self.Reset()

	def Ascend(self, ascension):
		if self.ascension < 7 and ascension >= 7:
			self.MaxHealth += self.AscendMaxHealth
		elif self.ascension >= 7 and ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
	'''
	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		if act 1:
			starts combat with chomp
			cannot use bellow 2 in a row
			cannot use thrash 3 time in a row
			cannot use chomp 2 times in a row
		if act 3:
			starts combat with the bellow power cast
			doesnt have to start with chomp
	'''

	def Chomp(self, paid):
		if self.ascension >= 2:
			damage = 12
		else:
			damage = 11
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Chomp to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you!")

	def Thrash(self, paid):
		damage = 7
		block = 5
		# Deal damage and gains block
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		barrier, targets = self.GainBlock(block, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Thrash to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you and gains RAW_INTENT:{block} --> ACTUAL:{barrier} block!")

	def Bellow(self, paid):
		block = 6
		if self.ascension >= 2 and self.ascension < 17:
			strength = 4
		elif self.ascension >= 17:
			strength = 5
			block = 9
		else:
			strength = 3
		# Gains strength and block
		# create or update a strength instance
		barrier, targets = self.GainBlock(block, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Bellow to gain {strength} and RAW_INTENT:{block} --> ACTUAL:{barrier} block!")


'''
Work in progress
Needs power cultist and ritual thing
'''

class Cultist(monsters.Monster):
	'''
	Known Parties:
		Act 1:
			Cultist
			Cultist, Louse
			Cultist, Acid Slime (M)
			Cultist, Spike Slime (M)
		Act 2:
			Cultist *3
			Cultist, Chosen
		Act 3:
			Cultist *2, Awakened One
	'''
	def __init__(self, ID="<TemplateSlaver>", Arena=None, Friendlies=None, ascension=0, act=1):
		# Ensure proper type
		ascension, act = int(ascension), int(act)
		# Constructor
		super().__init__(ID, Arena, Friendlies)
		self.Name = f"Cultist"
		self.Act = act
		# Stats
		self.MaxHealth = self.rng.randint(48, 54)
		self.AscendMaxHealth = 2
		# Moves
		self.makeMoves((powers.SOURCE.ATTACK, self.Dark_Strike, False, f"{str(self)} stabs"),
						(powers.SOURCE.POWER, self.Incantation, False, f"{str(self)} performs a ritual"))
		# Starts combat with Incantation (SpecialIntent)
		self.SpecialMoveSet((self.Dark_Strike, 1))

		# Ascend the mortal form
		self.ascension = ascension
		if ascension > 0:
			self.Ascend(ascension)
		# Call Reset to propagate everything properly
		self.Reset()

	def Ascend(self, ascension):
		if self.ascension < 7 and ascension >= 7:
			self.MaxHealth += self.AscendMaxHealth
		elif self.ascension >= 7 and ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
	'''
	def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
		TBD
	'''
	def Dark_Strike(self, paid):
		#Does damage to single target
		damage = 6
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Stab to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you!!")

	def Incantation(self, paid):
		#gains strength per tern
		if self.ascension >= 4 and self.ascension < 17:
			Ritual = 4
		elif self.ascension >= 17:
			Ritual = 5
		else:
			Ritual = 3
		"""
		self.ApplyPowers(ritualPower, affectClass=self.Abilities[self.Callbacks.index(self.Incantation)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=True, ArenaIncludeSelf=True, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=True, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
						extras=[])
		"""
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Incantation to gain Ritual {Ritual}!")

'''
work in progress
needs power curl up
'''
class Louse(monsters.Monster):
	'''
		Known Parties:
		Act 1:
			Louse *2
			Louse *3
			Louse, Cultist
			Louse, Looter
			Louse, Red Slaver
			Louse, Blue Slaver
			Louse, Jaw Worm
			Louse, Fungi Beast
	'''
	def __init__(self, ID="<TemplateSlaver>", Arena=None, Friendlies=None, ascension=0, variant=0):
		# Ensure proper type
		ascension, variant = int(ascension), int(variant)
		# Constructor
		super().__init__(ID, Arena, Friendlies)
		self.Color = ['Red', 'Green'][variant]
		self.Name = f"{self.Color} Louse"
		self.Act = 1
		# Stats
		self.BaseDamage = self.rng.randint(5,7)
		self.AscendMaxHealth = 1
		if self.Color == 'Red':
			self.MaxHealth = self.rng.randint(10, 15)
		else:
			self.MaxHealth = self.rng.randint(11, 17)
		# Moves
		self.makeMoves((powers.SOURCE.ATTACK, self.Bite, False, f"{str(self)} bites"),
						(powers.SOURCE.SKILL, self.Grow, False, f"{str(self)} gets larger"),
						(powers.SOURCE.SKILL, self.Spit_Web, False, f"{str(self)} spits web"))
		if self.Color == 'Red':
			self.SpecialMoveSet((self.Bite, 0.75),
								(self.Grow, 0.25))
		else:
			self.SpecialMoveSet((self.Bite, 0.75),
								(self.Spit_Web, 0.25))

		# Powers
		# self.PowerPool.append(Power(Curl Up)) # gain block after surviving hp loss
		# Ascend the mortal form
		self.ascension = ascension
		if ascension > 0:
			self.Ascend(ascension)
		# Call Reset to propagate everything properly
		self.Reset()

	def Reset(self):
		super().Reset()
		# Ensure curl up is available after resetting
		# self.PowerPool.append(Power(Curl Up))

	def Ascend(self, ascension):
		if self.ascension < 7 and ascension >= 7:
			self.MaxHealth += self.AscendMaxHealth
			self.Pattern = [0.4, 0.3, 0.3]
		elif self.ascension >= 7 and ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
			self.Pattern = [0.3, 0.4, 0.3]
	'''
		def SpecialIntent(self, moveCall, moveAlternatives, moveChances):
			TBD
	'''
	def Bite(self, paid):
		#Does damage to single target
		damage = self.BaseDamage
		if self.ascension >= 2:
			damage += 1
		# Deal damage
		dealt, targets = self.Damage(damage, ArenaTargets=paid, GroupTargets=paid)
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Bite to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you!!")

	def Grow(self, paid):
		# Just for Red Louse
		if self.ascension >= 17:
			strength = 4
		else:
			strength = 3
		'''
		# Apply strength to target
		strengthPower = powers.Power(timings=powers.TRIGGER.OFFENSE, priority=1, turns=None, callback=powers.STRENGTH, AffectDescription=powers.DESCRIPTIONS.STRENGTH)
		targets = self.ApplyPowers(strengthPower, affectClass=self.Abilities[self.Callbacks.index(self.Grow)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=True, ArenaIncludeSelf=True, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=True, GroupIncludeSelf=False, GroupAll=False, GroupCheckAlive=True,
						extras=[])
		'''
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Grow to apply {strength} strength to {[str(monster) for monster in targets]}!!")

	def Spit_Web(self, paid):
		weak = 2
		targets = self.ApplyPowers(powers.makeWeak(weak), affectClass=self.Abilities[self.Callbacks.index(self.Spit_Web)].affectClass,
						ArenaTargets=paid, ArenaOnlySelf=False, ArenaIncludeSelf=False, ArenaAll=False,
						GroupTargets=paid, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=True,
						extras=[])
		if settings.DEBUG.minimal <= settings.ARENA_DEBUG:
			print(f"{str(self)} uses Spit Web apply {weak} weak to {[str(monster) for monster in targets]}!!")

