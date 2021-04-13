objects = {}

import act_1_monsters as a1
objects.update(a1.objects())
#import act_2_monsters as a2
#objects.update(a2.objects())
#import act_3_monsters as a3
#objects.update(a3.objects())
#import act_4_monsters as a4
#objects.update(a4.objects())

def makeMonster(Type, **kwargs):
	return objects[Type](**kwargs)
