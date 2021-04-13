import arena, powers

def objects():
	return {"AcidSlime": AcidSlime}

"""
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
"""

class AcidSlime(arena.Monster):
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
		self.makeMoves((powers.SOURCE.ATTACK, self.Corrosive_Spit, f"{str(self)} spits"),
						(powers.SOURCE.ATTACK, self.Tackle, f"{str(self)} tackles"),
						(powers.SOURCE.SKILL, self.Lick, f"{str(self)} licks"))
		if self.Size == 'S':
			self.Pattern = [0, 0.5, 0.5]
		else:
			self.Pattern = [0.3, 0.4, 0.3]
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
			self.Pattern = [0.4, 0.3, 0.3]
		elif self.ascension >= 7 and self.ascension < 7:
			self.MaxHealth -= self.AscendMaxHealth
			self.Pattern = [0.3, 0.4, 0.3]

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

	def Corrosive_Spit(self):
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
		dealt, targets = self.Damage(damage)
		print(f"{str(self)} uses CORROSIVE_SPIT to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you and shuffle {n_slimed} into {[str(monster) for monster in targets]}'s discard!!")

	def Lick(self):
		if self.Size == 'L':
			weak = 2
		else: # self.Size == 'M' or 'S':
			weak = 1
		# Apply weak to target
		weaknessPower = powers.Power(timings=powers.TRIGGER.OFFENSE, priority=1, turns=weak, callback=powers.WEAK, AffectDescription=powers.DESCRIPTIONS.WEAK)
		targets = self.ApplyPowers(weaknessPower, affectClass=self.Abilities[self.Callbacks.index(self.Lick)].affectClass,
						ArenaTargets=1, ArenaSelf=False, ArenaAll=False,
						GroupTargets=1, GroupOnlySelf=False, GroupIncludeSelf=False, GroupAll=True, GroupCheckAlive=True,
						extras=[])
		print(f"{str(self)} uses LICK to apply {weak} weak to {[str(monster) for monster in targets]}!!")

	def Tackle(self):
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
		dealt, targets = self.Damage(damage)
		# How you would do a multihit:
		#damages = [damage, damage]
		#dealt, targets = self.Damage(*damages)
		print(f"{str(self)} uses TACKLE to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to {[str(monster) for monster in targets]}!!")

