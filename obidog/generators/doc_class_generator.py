from mako.template import Template
import os

def generate(cwd, class_data):
    class_name = class_data["name"]
    template_args = {
        "class_name": class_name
    }

    os.mkdir(os.path.join(cwd, "output"))
    with open("templates/lua_class.html") as template_source:
        with open(os.path.join(cwd, f"output/{class_name}.html"), "w") as template_export:
            template_export.write(Template(template_source.read()).render(
                **template_args
            ))