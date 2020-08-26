import os

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from obidog.models.classes import ClassModel
from obidog.documentation.config import WEBSITE_URL, DOC_PATH

DB_FILENAME = "search.json"
CURRENT_VERSION = "0.5"  # TODO: Fetch version from ObEngine repo


class LuaClass:
    def __init__(
        self, name, cpp_name, lua_name, description, attributes, methods, helper=None
    ):
        self.type = "class"
        self.name = name
        self.cpp_name = cpp_name
        self.lua_name = lua_name
        self.description = description
        self.attributes = attributes
        self.methods = methods

        self.helper = helper


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
        self.type = "function"
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
        self.type = "parameter"
        self.name = name
        self.type = type
        self.description = description


fn_example = """local collider = Engine.Scene:createCollider("test");
collider:addTag(obe.Collision.ColliderTagType.Tag, "character");
collider:removeTag(obe.Collision.ColliderTagType.Tag, "character");"""
removeTag = LuaFunction(
    name="removeTag",
    signature="nil obe.Collision.PolygonalCollider.removeTag(obe.Collision.ColliderTagType tagType, string tag)",
    description="Removes a Tag of the Collider.",
    parameters=[
        LuaParameter(
            name="tagType",
            type="obe.Collision.ColliderTagType",
            description="List you want to remove a Collider from (Tag / Accepted / Rejected)",
        ),
        LuaParameter(
            name="tag", type="string", description="Name of the Tag you want to remove"
        ),
    ],
    return_type="nil",
    example=fn_example,
    doxygen_url="https://obengine.io/doc/cpp/classobe_1_1_collision_1_1_polygonal_collider.html#a972819e978772fbcf1ec3b25ddb124a8",
    source_url="https://github.com/Sygmei/ObEngine/blob/master/src/Core/Collision/PolygonalCollider.cpp#L170",
    bindings_url="https://github.com/Sygmei/ObEngine/blob/master/src/Core/Bindings/obe/Collision/Collision.cpp#L71",
)
PolygonalCollider = LuaClass(
    name="PolygonalCollider",
    cpp_name="obe::Collision::PolygonalCollider",
    lua_name="obe.Collision.PolygonalCollider",
    description="Class used for all Collisions in the engine, it's a Polygon containing n points",
    attributes=[],
    methods=[removeTag, removeTag, removeTag, removeTag, removeTag],
    helper="Lib/Internal/CollisionHelper.lua",
)

lookup = TemplateLookup(["templates/documentation"])


def document_class(class_value: ClassModel):
    directory = os.path.join("export", *class_value.namespace.split("::"))
    os.makedirs(directory, exist_ok=True)
    with open(
        os.path.join(directory, f"{class_value.name}.html"), "w", encoding="utf-8",
    ) as export:
        with open(
            "templates/documentation/lua_body.mako", "r", encoding="utf-8"
        ) as tpl:
            try:
                export.write(
                    Template(tpl.read(), lookup=lookup).render(
                        target=class_value,
                        DB_LOCATION=f"{WEBSITE_URL}/{DOC_PATH}/{DB_FILENAME}",
                        CURRENT_VERSION=CURRENT_VERSION,
                    )
                )
            except Exception as e:
                export.write(exceptions.html_error_template().render().decode("utf-8"))


def document_namespace(namespace):
    directory = os.path.join("export", *namespace.path.split("::"))
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, f"index.html"), "w", encoding="utf-8",) as export:
        with open(
            "templates/documentation/lua_body.mako", "r", encoding="utf-8"
        ) as tpl:
            try:
                export.write(
                    Template(tpl.read(), lookup=lookup).render(
                        target=namespace,
                        DB_LOCATION=f"{WEBSITE_URL}/{DOC_PATH}/{DB_FILENAME}",
                        CURRENT_VERSION=CURRENT_VERSION,
                    )
                )
            except Exception as e:
                export.write(exceptions.html_error_template().render().decode("utf-8"))
