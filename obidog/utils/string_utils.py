import re
import inflection


def clean_capitalize(string):
    return re.sub("([a-zA-Z])", lambda x: x.groups()[0].upper(), string, 1)


def format_name(name):
    return inflection.underscore(name)


def format_filename(name):
    return inflection.camelize(name)
