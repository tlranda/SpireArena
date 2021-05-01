# SpireArena
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
* Implementing statuses and how they interact with monster intents
* Add a block parameter to abstract monsters
* Default monster powers:
	* Start of Turn: Lose all block unless you have the Barrier power
	* On death: Announce death, mark dead in group

Labor TODO:
* Implementing powers/monsters from the game

