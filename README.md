# SpireArena

# Ceased Development Notice: This version proved troublesome to design, and is no longer actively maintained

Slay The Spire Monster Infighting... Who would win?

STRUCTURE:
* test\_arena.py: Main controller, run as `python3 test_arena.py -h` to learn more
* demo.py: Small test file for replicating small-scale experiments
* SpireArenaLib: The actual library
	+ arena.py: Abstract Classes and templates
	+ monsters.py: Master monster import file
	+ powers.py: Abstract powers and power implementations
	+ act\_\#\_monsters.py: Implementation for monsters from Act #
	+ settings.py: Global settings for the library as a whole
* Sample\_Monsters: Directory of files with potential monster groups to load into your brawls
	+ sample\_monsters.txt: Two Large AcidSlimes at ascension 0
	+ sample\_monsters\_vs.txt: Three Medium AcidSlimes at ascension 17
	+ single\_slime\_1.txt: One Large AcidSlime at ascension 17
	+ single\_slime\_2.txt: One Medium AcidSlime at ascension 2

Design TODO:
* More basic StS power implementations: Vulnerable, Frail, Thorns, Strength/Shackles
* Entanglement requires other means to cancel moves, may play into how statuses operate (chance to apply status to move portion targeting creature?)
    * Monsters '''draw''' 5 cards a turn, with 2+Act energy to play them (default 1 cost per card). During a turn, monsters can spend these resources.
	* By default, monsters ONLY PLAY 1 card, but it costs +1 energy to target more enemies.
	* When a monster draws a status, it triggers a % chance that a potentially targetable enemy ends up being untargetable
* Implementing statuses and how they interact with monster intents
* For artifact tags to work, one of two things:
	* Assume that enemies do not buff one another and artifact prevents incoming power, but friendlies buff so allow incoming power
	* Rework power class to have buff/debuff tags to guarantee the artifact charges work as intended
* Moveset swapping, moveset disabling
* Darkling madness
* Reacting to plays of any/all types
* Group total ordering for surrounding and back attacks

Labor TODO:
* Implementing powers/monsters from the game
* Act 1 monsters: Adding Slime Splits, Thief Escapes, Entanglement, Enrage
  + Act 1 elites: Also enrage, asleep, metallicize, strength down, dexterity down, Artifact
  + Act 1 bosses: Also defensive/offensive modes
* Act 2 monsters: Adding Flying, Hexing, Plated Armor, Healing, Malleable, Confusion
  + Act 2 elites: Also summon monsters, painful stabs
  + Act 2 bosses: Also stasis
* Act 3 monsters: Adding Lifelink/Regrow/Revive, Thorns, Explode, Constricted, Fading, Shifting, ?Reactive?
  + Act 3 elites: Also slow, intangible
  + Act 3 bosses: Also curiosity, time warp, draw reduction
* Act 4 monsters: Adding surrounded, back attack
  + Act 4 bosses: Also beat of death, invincible
  + Act 4 empowered elites: Also regeneration
