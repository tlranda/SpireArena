import arena

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
		self.Abilities = [self.Corrosive_Spit, self.Tackle, self.Lick]
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
			ForbiddenIdx = self.Abilities.index(self.Tackle)
			ForbiddenMove = self.Tackle
		elif self.Size == 'M' and self.ascension >= 17:
			ForbiddenIdx = self.Abilities.index(self.Lick)
			ForbiddenMove = self.Lick
		elif self.Size == 'S':
			if self.ascension >= 17 and len(self.History) == 0:
				# Has to start on lick
				moveCall = self.Lick
				print(f"{self.Name} {self.ID} must initiate combat with 'Lick'")
			elif self.ascension >= 2 and len(self.History) > 0:
				# Alternates between Lick and Tackle moves
				prevCall = moveCall
				moveCall = self.Lick if self.History[(self.HistoryIdx-1)%2] == self.Abilities.index(self.Tackle) else self.Tackle
				if prevCall != moveCall:
					print(f"{self.Name} {self.ID} must alternate between moves")
			return moveCall
		if moveCall == ForbiddenMove:
			if len(self.History) >= 1 and self.History[(self.HistoryIdx-1)%2] == ForbiddenIdx:
				print(f"{self.Name} {self.ID} is prohibited from using '{ForbiddenMove.__name__}' twice in a row")
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
		dealt = self.Damage(damage)
		print(f"{self.Name} {self.ID} uses CORROSIVE_SPIT to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you and shuffle {n_slimed} into your discard!!")

	def Lick(self):
		if self.Size == 'L':
			weak = 2
		else: # self.Size == 'M' or 'S':
			weak = 1
		# Apply weak to target
		print(f"{self.Name} {self.ID} uses LICK to apply {weak} weak to you!!")

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
		dealt = self.Damage(damage)
		print(f"{self.Name} {self.ID} uses TACKLE to deal RAW_INTENT:{damage} --> ACTUAL:{dealt} damage to you!!")

