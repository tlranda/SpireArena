import enum, settings

"""
	TODO: Powers need trigger locks to prevent them from re-triggering
		* On same target (multihit)
		* On base damage for different targets (aoe)
"""

"""
	Sources describe where effects come from in case that matters
	ie: Thorns only respond to attacks
"""
class SOURCE(enum.Enum):
	ATTACK = enum.auto()
	SKILL = enum.auto()
	POWER = enum.auto()
	FX = enum.auto()

"""
	Triggers describe events that occur in the game and can be responded to
	It's a poor man's listener API because event-driven is hard and I'm dumb
"""
class TRIGGER(enum.Enum):
	OFFENSE = enum.auto()         # interact with DAMAGE OUTPUT from SOURCE (weak, strength, shackles)
	DEFENSE = enum.auto()         # interact with DAMAGE MITIGATION at TARGET (vulnerable, block, intangible, frail)
	REGEN = enum.auto()           # involve LIFE GAIN at EITHER endpoint (regen, heals, resurrection)
	ON_DEATH = enum.auto()        # occur when the TARGET creature is killed
	"""
	Solution to Darkling Nonsense:
		Unlimited turn power with ON_DEATH trigger that CREATES and ASSIGNS a new
		countdown timer and another TRIGGER.
		The timer is just the 3-turn (or whatever length) timer and doesn't actually do
		anything other than tick down per turn.
		The TRIGGER power is an ON_POWER_LOSE looking for that timer expiring, and calls
		the darkling slime's half-rez ability
	"""
	ON_KILL = enum.auto()         # occur when the SOURCE creature performs a kill
	ON_ATTACK = enum.auto()       # occur when the SOURCE creature performs an attack
	VS_ATTACK = enum.auto()       # occur when the TARGET creature is attacked (does not require damage to be dealt)
	ON_SKILL = enum.auto()        # occur when the SOURCE creature performs a skill
	VS_SKILL = enum.auto()        # occur when the TARGET creature has a skill performed against it
	ON_POWER_GAIN = enum.auto()   # occur when the SOURCE creature gains powers
	VS_POWER_GAIN = enum.auto()   # occur when the TARGET creature sees a power gained by SOURCE creature
	ON_POWER_LOSE = enum.auto()   # occur when the SOURCE creature loses a power
	VS_POWER_LOSE = enum.auto()   # occur when the TARGET creature sees a power lost by SOURCE creature
	ON_TURN = enum.auto()         # occurs at the start of SOURCE creature's turn (NO TARGET CREATURE)
	ON_PLAY = enum.auto()         # occurs when the SOURCE creature performs any play action (NO TARGET, but should use Group/Arena for VS_PLAY
	ON_HP_REDUCE = enum.auto()    # occurs when the TARGET creature's HP is reduced (thorns/malleable procs)
	VS_HP_REDUCE = enum.auto()    # occurs when the SOURCE creature deals HP damage to its target
	TURN_START = enum.auto()      # occurs when the SOURCE creature begins its turns
	TURN_END = enum.auto()        # occurs when the SOURCE creature ends its turns

affectLookup = {SOURCE.ATTACK: [TRIGGER.ON_ATTACK, TRIGGER.VS_ATTACK, TRIGGER.ON_PLAY],
				SOURCE.SKILL: [TRIGGER.ON_SKILL, TRIGGER.VS_SKILL, TRIGGER.ON_PLAY],
				SOURCE.POWER: [TRIGGER.ON_POWER_GAIN, TRIGGER.VS_POWER_GAIN, TRIGGER.ON_PLAY],
				SOURCE.FX: [TRIGGER.ON_PLAY]}

"""
	FOR INTERNAL USE (THIS FILE) ONLY

	Just make descriptions a string-Enum so that they're all defined in one place.
	Technically also makes localization possible but we're unlikely to ever have
	ppl who want that.
	But the localization angle is why this isn't a dictionary... eventually this
	should load from pickle files or something
"""
class DESCRIPTIONS():
	WEAK = "Reduce attack damage by 25%"
	SHACKLES = "Reduce Strength for 1 turn by 1 per stack"
	STRENGTH = "Increase damage by 1 per stack"
	VULNERABLE = "Increase attack damage by 50%"
	INTANGIBLE = "Reduce attack damage to 1"
	BLOCK = "Reduce attack damage by 1 per stack, then remove that many stacks"
	BARRICADE = "Block is not removed at the start of turns"
	BLOCK_LOSS_TURN_START = "Block is removed at the start of turns"
	DEAD = "Non-combat state"

"""
Revision note for powers:
	* All powers come in three flavors:
		+ They stick around forever and have a value that increments/decrements whatever
		+ They stick around for a set number of turns and the # of turns stacks
		+ They stick around for exactly 1 turn and the value increments/decrements (often in pairs ie: temporary strength, shackles)
	So just make these things happen instead

#0 PowerObject (Abstract)
	SHOULD ONLY BE USED INTERNALLY BY THIS FILE--USE makePower() TO INSTANCE POWER OBJECTS EXTERNALLY

	Defines an API for events in the fight:
		* Timing variants for ALL (BEFORE, ON, AFTER) : When to accept the event occurring
	Instanceable Examples of Enum classes
		* OffensePowers
			# Priority Order: Strength (3), Shackles (2), Weak (1)
		* DefensePowers
			# Priority Order: Vulnerable (3), Intangible (2), Block (use, 1)
		* UtilityPowers
			# On kill/death
				# FungiCombust
			# On/Vs attack/skill/power gain/power lose
				# Thorns, Chosen Hex, Awoken Phase 1
			# On HP reduction
				# Malleable
			# On turn
				# Lagavulin, OrbWalker
			# On play
				# Giant Head, TimeEater
			# On/Vs hp reduce
				# Transient

	ATTRIBUTES:
		turns : Int (turns to live) or None (permanent)
		priority : Int (higher # == higher priority)
		triggers : List of POWER classes to activate on
		removeOnDeath : Bool
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
	def __init__(self, timings, priority, turns, callback, callback2=None, PrepareDescription=None, AffectDescription=None, removeOnDeath=True):
		if type(timings) is not list:
			try:
				timings = list(timings)
			except TypeError: # Just a single one
				timings = [timings]
		self.triggers = timings
		self.priority = priority
		self.turns = turns
		self.removeOnDeath = removeOnDeath
		self.PrepareDescription = PrepareDescription
		self.AffectDescription = AffectDescription
		self.Affect = callback
		if callback2 is not None:
			# Override self.Prepare()
			self.Prepare = callback2
		self.name = self.Affect.__name__

	def __str__(self):
		turns_left = "infinity" if self.turns is None else str(self.turns)
		prepare = "" if self.PrepareDescription is None else f"Prepare: \"{self.PrepareDescription}\""
		affect = "" if self.AffectDescription is None else f"Affect: \"{self.AffectDescription}\""
		if prepare == "" and affect == "":
			definition = ""
		else:
			if prepare == "":
				definition = affect
			else:
				definition = prepare+", "+affect
			definition = ", "+definition
		return f"{self.name} [Priority {self.priority}, {turns_left} turns left{definition}]"

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

# Implement Powers as callbacks, and make API to properly implement the common cases
# TRIGGER.OFFENSE
def WEAK(value, affectClass, source, target, *extra):
	"""
		Value = Incoming->Outgoing Damage (Reduced by 25%, round down)
		Side Effects: None
	"""
	return int(value * 0.75)
def makeWeak(turns):
	return Power(timings=TRIGGER.OFFENSE, priority=1, turns=turns, callback=WEAK, AffectDescription=DESCRIPTIONS.WEAK)

def SHACKLES(value, affectClass, source, target, *extra):
	"""
		Value = Incoming->Outgoing Damage (reduced by extra[0]--the shackle amount)
		Extra = ShackleAmount (use negative value for temporary strength but I don't think any monsters have that)
		Side Effects: None
	"""
	return max(0, value-extra[0])
def makeShackles(strengthDown):
	def tempCallback(self, addShackles=0):
		"""
			Ok so here's maybe how prepared callbacks will work
			They should default all non-self arguments to whatever effectively does nothing
			They should return EVERYTHING that needs to be in the *extra for the Affect callback
			Then all power invocations on Affect() need to include a call to power.Prepare() at the end
		"""
		try:
			self.magic += addShackles
		except AttributeError:
			self.magic = addShackles
		return self.magic
	shacklesPower = Power(timings=TRIGGER.OFFENSE, priority=2, turns=1, callback=SHACKLES,
							callback2=tempCallback, AffectDescription=DESCRIPTIONS.SHACKLES)
	shacklesPower.Prepare(strengthDown)
	return shacklesPower

def STRENGTH(value, affectClass, source, target, *extra):
	"""
		Value = Incoming->Outgoing Damage (increased by extra[0]--strength value)
		Extra = StrengthAmount
		Side Effects: None
	"""
	return value+extra[0]
def makeStrength(strength):
	def tempCallback(self, addStrength=0):
		try:
			self.magic += addStrength
		except AttributeError:
			self.magic = addStrength
		return self.magic
	strengthPower = Power(timings=TRIGGER.OFFENSE, priority=3, turns=None, callback=STRENGTH,
					callback2=tempCallback, AffectDescription=DESCRIPTIONS.STRENGTH)
	strengthPower.Prepare(strength)
	return strengthPower

# TRIGGER.DEFENSE
def VULNERABLE(value, affectClass, source, target, *extra):
	"""
		TRIGGER should be TRIGGER.DEFENSE
		Priority should be 3
		Value = Outgoing Damage
		Increase by 50% (round down)
		Side Effects: None
	"""
	return int(value * 1.5)
def makeVulnerable(turns):
	return Power(timings=TRIGGER.OFFENSE, priority=1, turns=turns, callback=WEAK, AffectDescription=DESCRIPTIONS.WEAK)

def INTANGIBLE(value, affectClass, source, target, *extra):
	"""
		TRIGGER should be TRIGGER.DEFENSE
		Priority should be 2
		Value = Outgoing Damage
		Reduce to 1
		Side Effects: None
	"""
	return min(value, 1)
def makeIntangible(turns):
	return Power(timings=TRIGGER.DEFENSE, priority=2, turns=turns, callback=INTANGIBLE, AffectDescription=DESCRIPTIONS.INTANGIBLE)

def BLOCK(value, affectClass, source, target, *extra):
	"""
		TRIGGER should be TRIGGER.DEFENSE
		Priority should be 2
		Turns should be None (This is not the BLOCK GAIN trigger, this is the BLOCK USE trigger -- it is ALWAYS ON)
		Value = Outgoing Damage
		Side Effects: Reduce BlockAmount in target by blocked amount
	"""
	if settings.DEBUG.full == settings.ARENA_DEBUG:
		print("\t\t"+f"{str(source)} sends {value}, {str(target)} has {target.Block}")
	available_block = target.Block
	blocked_damage = min(value, available_block)
	value -= blocked_damage
	target.Block = available_block - blocked_damage
	return value
def makeBlock():
	return Power(timings=TRIGGER.DEFENSE, priority=2, turns=None, callback=BLOCK, AffectDescription=DESCRIPTIONS.BLOCK)

# Some powers only need to be present, they don't do anything themselves but their presence affects how other powers work
# Supply integer number of turns to make this functionally operate as blur
def makeBarricade(turns=None):
	timing = list()
	return Power(timings=timing, priority=0, turns=turns, callback=None, AffectDescription=DESCRIPTIONS.BARRICADE)
# The power that cares about barricade existing -- a trigger to remove block at the start of each turn
def BLOCK_LOSS_TURN_START(value, affectClass, source, target, *extra):
	"""
		TRIGGER should be TRIGGER.TURN_START
		Priority should be 0
		Turns should be None (always on, checks for barricades on source)
		Side Effects: Reduces block to 0 if no Barricade present
	"""
	barricade = False
	for power in source.PowerPool:
		if power.AffectDescription == DESCRIPTIONS.BARRICADE:
			barricade = True
	if settings.DEBUG.full == settings.ARENA_DEBUG:
		print("\t\t"+f"{str(source)} has {source.Block} at start of turn and {'does not have' if not barricade else 'has'} barricade")
	if not barricade:
		source.Block = 0
	return not barricade
def makeBlockLossEachTurn():
	return Power(timings=TRIGGER.TURN_START, priority=0, turns=None, callback=BLOCK_LOSS_TURN_START, AffectDescription=DESCRIPTIONS.BLOCK_LOSS_TURN_START)

def die(value, affectClass, source, target, *extra):
	"""
		TRIGGER should be TRIGGER.ON_HP_REDUCE
		Priority should be 0
		Turns should be None (always on, checks for death)
		Side Effects: Marks as dead when HP reduced to/below 0
	"""
	if target.Health <= 0 and target.Alive:
		target.Alive = False
		# Mark dead in group, handle group death
		if target.Friendlies is not None:
			target.Friendlies.fight_on -= 1
		# Because darkling slimes exist, on death should also kill MOST other powers
		# but powers should have a (default on) field indicating that they get removed
		# with the on-death call. any power turning that off should be VERY intentional
		# about it
		# Trigger any monster-defined/applied on-death effects
		triggers = [TRIGGER.ON_DEATH]
		target.Empower(None, SOURCE.FX, *triggers, source=source, target=target, extras=None)
		triggers = [TRIGGER.ON_KILL]
		source.Empower(None, SOURCE.FX, *triggers, source=source, target=target, extras=None)
	elif settings.DEBUG.full == settings.ARENA_DEBUG:
		print("\t\t"+f"{str(target)} does not die")
	return value
def makeDie():
	return Power(timings=TRIGGER.ON_HP_REDUCE, priority=0, turns=None, callback=die, AffectDescription=DESCRIPTIONS.DEAD)

powerDict = {	'weak': makeWeak,
				'shackles': makeShackles,
				'strength': makeStrength,
				'vulnerable': makeVulnerable,
				'intangible': makeIntangible,
				'block': makeBlock,
				'barricade': makeBarricade,
				'blockLossEachTurn': makeBlockLossEachTurn,
				'die': makeDie,
			}
def makePower(powerName, *powerValues):
	return powerDict[powerName](*powerValues)

