from django import template
import sys

register = template.Library()

@register.filter
def get(dictionary, key):
    return dictionary.get(key)

@register.filter
def pertinent_values(dictionary, key):
    keys = dictionary.keys()
    print >>sys.stderr, keys
    keys.sort(lambda a, b: cmp(dictionary[b][key], dictionary[a][key]))
    if len(key) < 20:
        return keys
    value = dictionary[keys[20]][key]
    print >>sys.stderr, value
    index = 19
    while dictionary[keys[index]][key] > value and index > 10:
        index -= 1
    if index == 10:
        index = 19
    return keys[:index + 1]
