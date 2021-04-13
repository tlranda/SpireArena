# SpireArena
Slay The Spire Monster Infighting... Who would win?

STRUCTURE:
* test_arena.py: Main controller, run as `python3 test_arena.py -h` to learn more
* demo.py: Small test file for replicating small-scale experiments
* arena.py: Abstract Classes and templates
* act_#_monsters.py: Implementation for monsters from Act #
* monsters.py: Master monster import file
* powers.py: Abstract powers and power implementations
* Sample_Monsters: Directory of files with potential monster groups to load into your brawls
	+ sample_monsters.txt: Two Large AcidSlimes at ascension 0
	+ sample_monsters_vs.txt: Three Medium AcidSlimes at ascension 17
	+ single_slime_1.txt: One Large AcidSlime at ascension 17
	+ single_slime_2.txt: One Medium AcidSlime at ascension 2

Design TODO:
* Implementing statuses and how they interact with monster intents
* Add a block parameter to abstract monsters
* Default monster powers:
	* Start of Turn: Lose all block unless you have the Barrier power
	* On death: Announce death, mark dead in group
Labor TODO:
* Implementing powers/monsters from the game
