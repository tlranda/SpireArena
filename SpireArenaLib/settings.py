import enum
from functools import total_ordering

@total_ordering
class DEBUG(enum.Enum):
	# note that successive enum.auto() ascends, so needs to be ordered Lowest->Highest levels
	none = enum.auto()
	minimal = enum.auto()
	full = enum.auto()
	def __eq__(self, other):
		if type(other) is int:
			return self.value == other
		elif type(other) is DEBUG:
			return self.value == other.value
		else:
			raise TypeError("Only compare between ints")
	def __ge__(self, other):
		if type(other) is int:
			return self.value >= other
		elif type(other) is DEBUG:
			return self.value >= other.value
		else:
			raise TypeError("Only compare between ints")
	def __hash__(self):
		return self.value

# Controls output in other files
debug_names=dict((e.name,e.value) for e in DEBUG)
reverse_debug_names=dict((v,k) for k,v in zip(debug_names.keys(), debug_names.values()))
debug_levels=dict((e,e.value) for e in DEBUG)
reverse_debug_levels=dict((v,k) for k,v in zip(debug_levels.keys(), debug_levels.values()))
ARENA_DEBUG=debug_names['full']

