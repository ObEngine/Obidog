import os
import re

OBENGINE_DOCUMENTATION_URL = os.environ.get(
    "OBENGINE_DOCUMENTATION_URL", 
    "https://obengine.io/doc/cpp")

def class_name_to_doc_link(name):
    if name.startswith("obe::"):
        transformed_name = "class" + name.replace("::", "_1_1_")
        #import pdb; pdb.set_trace()
        while re.search(r"([a-z]|[A-Z])[A-Z]", transformed_name):
            transformed_name = re.sub(
                r"((?P<f>[a-z]|[A-Z])(?P<s>[A-Z]))", 
                r"\g<f>_\g<s>", 
                transformed_name)
        transformed_name = transformed_name.lower()
        transformed_name += ".html"
        return "/".join([OBENGINE_DOCUMENTATION_URL, transformed_name])