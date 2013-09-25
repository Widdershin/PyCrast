def startswithrep(s):
	if s == "":
		return False
	return startswithold(s)

print "Test".startswith("")

startswithold = str.startswith
str.startswith = startswithrep

print "Test".startswith("")