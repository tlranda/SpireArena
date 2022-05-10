MoveSet logic will require a "frustration" turn pass if no moves are available.

Modifies incoming:
* Artifact
	+ Simply deny an incoming augment application and decrement
* Vulnerable / Flying / Invincible / Intangible
	+ Simply interact

Modifies outgoing:
* Weak / Frail
	+ Simply interact
* Strength / Shackles / Dexterity
	+ Simply interact

Replies to incoming:
* Thorns / Malleable / Explode
	+ Neutral responses
* Enrage / Hex / Slow / Beat of Death / Curiosity / Shifting (writhing mass)
	+ Inspect Limbo and report back as needed

End of turn:
* Metallicize / Plated Armor (also replies to incoming) / Healing / Regeneration
	+ Simply interact
* Barricade
	+ Cancel Limbo move
* Fading
	+ Exit battle using Escape
* Constricted
	+ Neutral trigger on End of Turn

Moveset Interaction (Status)
* Entangle / Asleep / Stasis / Moveset Shift (defensive mode, offensive mode)
	+ Moveset Shifts in general operate by a PowerPipelineEvent touching monster Status, triggering the appropriate Moveset Shift to be transitioned in a set number of turns (0 for immediate)
		* Entangle is applied to an enemy, and reads their current MoveSet. It caches this and tells them to restore it in 2 turns, and in 1 turn to move to a modified moveset that lacks attack moves.
		* Asleep waits to see HP decrease, and instantly swaps for agressive movement
		* Stasis reads the monster's current moveset and caches it in the stasis monster, then gives them a 0 turn copy without that move.
* Escape / Fading / LifeLink
	+ These are timer-ish moveset status that tell monsters to exit the battle (self-KO) when conditions are met
	+ In LifeLink's particular case, the status can tell a dead monster to make itself untargetable for 1 turn, then create a transition to revive at half HP. When making untargetable, if all other LifeLinked monsters are present it removes all revives and properly denotes all LifeLinks as dying.
* Fall (from flying)
	+ Cancels all moves for one turn
* Splits / Summon Monsters
	+ Create new allied monster instances
* Confusion / Painful Stabs / Time Warp / Draw Reduction
	+ These limit player capabilities on turns, which can be represented by disabling a number of moves (similar to stasis/entangle) for a short time with a (perhaps random) amount of lag in applying the move.

Possibly Ignored:
* Surrounded / Back Attack
