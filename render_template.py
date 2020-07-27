from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions


class LuaClass:
    def __init__(self, functions):
        self.functions = functions


class LuaFunction:
    def __init__(
        self,
        name,
        signature,
        description,
        parameters,
        return_type,
        example,
        doxygen_url,
        source_url,
        bindings_url,
    ):
        self.name = name
        self.signature = signature
        self.description = description
        self.parameters = parameters
        self.return_type = return_type
        self.example = example
        self.doxygen_url = doxygen_url
        self.source_url = source_url
        self.bindings_url = bindings_url


class LuaParameter:
    def __init__(self, name, type, description):
        self.name = name
        self.type = type
        self.description = description


fn_example = """local collider = Engine.Scene:createCollider("test");
collider:addTag(obe.Collision.ColliderTagType.Tag, "character");
collider:removeTag(obe.Collision.ColliderTagType.Tag, "character");"""
removeTag = LuaFunction(
    "removeTag",
    "nil obe.Collision.PolygonalCollider.removeTag(obe.Collision.ColliderTagType tagType, string tag)",
    "Removes a Tag of the Collider.",
    [
        LuaParameter(
            "tagType",
            "obe.Collision.ColliderTagType",
            "List you want to remove a Collider from (Tag / Accepted / Rejected)",
        ),
        LuaParameter("tag", "string", "Name of the Tag you want to remove"),
    ],
    "nil",
    fn_example,
    "",
    "",
    "",
)
PolygonalCollider = LuaClass([removeTag])

lookup = TemplateLookup(["templates"])

with open("export.html", "w", encoding="utf-8") as export:
    with open("templates/lua_body.mako", "r", encoding="utf-8") as tpl:
        try:
            export.write(
                Template(tpl.read(), lookup=lookup).render(klass=PolygonalCollider)
            )
        except Exception as e:
            print("ERROR")
            export.write(exceptions.html_error_template().render().decode("utf-8"))
