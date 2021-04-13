from arena import Arena, MonsterGroup
from act_1_monsters import AcidSlime
field = Arena(ID="SpireArena")
groups = [MonsterGroup(), MonsterGroup()]
field.AddGroups(*groups)
for group, name in zip(groups, [str(_+1) for _ in range(len(groups))]):
	group.AddMonster(AcidSlime(f"slime_{name}", field, group))
for _ in range(10):
	field.Turn()
