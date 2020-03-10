import re

def clean_capitalize(string):
    return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), string, 1)