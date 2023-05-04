import re
import string

import inflection


def clean_capitalize(string):
    return re.sub("([a-zA-Z])", lambda x: x.groups()[0].upper(), string, 1)


def format_name(name):
    return inflection.underscore(name)


def format_filename(name):
    return inflection.camelize(name)


class FormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def partial_format(string_input: str, **kwargs):
    formatter = string.Formatter()
    mapping = FormatDict(**kwargs)
    return formatter.vformat(string_input, (), mapping)


def replace_delimiters(
    input_string: str,
    from_delimiter: str,
    to_opening_delimiter: str,
    to_closing_delimiter: str,
) -> str:
    opening = True
    final_string = []
    for ch in input_string:
        if ch == from_delimiter:
            final_string.append(
                to_opening_delimiter if opening else to_closing_delimiter
            )
            opening = not opening
        else:
            final_string.append(ch)
    return "".join(final_string)
