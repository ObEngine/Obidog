import json
import os
import re

CLASS_REGEX = re.compile(
    r"""
\(\s*\*lua\s*\)\s*
(?P<class_path>\[\".+\"\])
\.setClass\(\s*kaguya::UserdataMetatable
<\s*(?P<class_name>([^,>])+)\s*
(,\s*(?P<class_parents>([^>]\s*)+)\s*>)?
(,\s*(?P<class_parent>.+)\s*)?
\s*>
\s*\(\s*\)(?P<class_body>[^;]*)\);
""".replace(
        "\n", ""
    )
)

METHOD_REGEX = re.compile(
    r"""
\.addFunction\(\s*
\"(?P<method_name>[^\"]+)\"
,\s*(?P<method_funcptr>[^.]+)\)
""".replace(
        "\n", ""
    )
)

OVERLOADED_METHOD_REGEX = re.compile(
    r"""
\.addOverloadedFunctions\(\s*
\"(?P<method_name>[^\"]+)\"
,\s*(?P<method_funcptrs>[^.]+)\)
""".replace(
        "\n", ""
    )
)

PROPERTY_REGEX = re.compile(
    r"""
\.addProperty\(\s*
\"(?P<property_name>[^\"]+)\"
,\s*(?P<property_ptr>[^.]+)\)
""".replace(
        "\n", ""
    )
)

MEMBER_FUNCTION_OVERLOADS_REGEX = re.compile(
    r"""
KAGUYA_MEMBER_FUNCTION_OVERLOADS\(\s*
(?P<wrapper_name>\w+)\s*
,\s*(?P<wrapped_class>[\w:]+)\s*
,\s*(?P<wrapped_method>[\w:]+)\s*
,\s*(?P<min_args>\d+),
\s*(?P<max_args>\d+)\s*\);
""".replace(
        "\n", ""
    )
)

LAMBDA_REGEX = re.compile(
    r"""
\(\s*\*lua\s*\)\s*
(?P<lambda_path>\[\".+\"\])\s*
=\s*kaguya::function
\(\s*\[(?P<lambda_capture>[^]]*)\]\s*
\((?P<lambda_parameters>[^)]*)\)\s*
{\s*(?P<lambda_code>\s*.+\s*)\s*}\s*\)\s*;
""".replace(
        "\n", ""
    )
)

FUNCTION_REGEX = re.compile(
    r"""
\(\s*\*lua\s*\)\s*
(?P<function_path>\[\".+\"\])\s*
=\s*kaguya::function
\(\s*(?P<function_ref>[^]});]+)
\s*\)\s*;
""".replace(
        "\n", ""
    )
)

VARIABLE_REGEX = re.compile(
    r"""
\(\s*\*lua\s*\)\s*
(?P<variable_path>\[\".+\"\])\s*
=\s*(?P<variable_ref>[^]});]+);
""".replace(
        "\n", ""
    )
)


def insert_path_to_dict(tree, path, value):
    splitted_path = path.split(".")
    for i, path_part in enumerate(splitted_path):
        if i == len(splitted_path) - 1:
            tree[path_part] = value
            break
        elif not path_part in tree:
            tree[path_part] = {}
        tree = tree[path_part]


def path_to_lua_name(classpath):
    return classpath.replace('"]["', ".").replace('["', "").replace('"]', "")


def parse_lua_variable_binding(variable_definition):
    variable_path = variable_definition.group("variable_path")
    lua_name = path_to_lua_name(variable_path)
    variable_reference = variable_definition.group("variable_ref")

    return {"type": "variable", "lua_name": lua_name, "reference": variable_reference}


def parse_lua_function_binding(function_definition):
    function_path = function_definition.group("function_path")
    lua_name = path_to_lua_name(function_path)
    function_reference = function_definition.group("function_ref")

    return {"type": "function", "lua_name": lua_name, "reference": function_reference}


def parse_lua_class_binding(class_definition):
    class_name = class_definition.group("class_name")
    class_path = class_definition.group("class_path")
    lua_name = path_to_lua_name(class_path)
    class_body = class_definition.group("class_body")
    methods = {}
    properties = {}
    for method_definition in re.finditer(METHOD_REGEX, class_body):
        method_name = method_definition.group("method_name")
        method_funcptr = method_definition.group("method_funcptr")
        methods[method_name] = {
            "name": method_name,
            "function_ptr": method_funcptr,
            "overloaded": False,
        }
    for ov_method_definition in re.finditer(OVERLOADED_METHOD_REGEX, class_body):
        method_name = ov_method_definition.group("method_name")
        method_funcptrs = ov_method_definition.group("method_funcptrs")
        methods[method_name] = {
            "name": method_name,
            "function_ptr": method_funcptrs,
            "overloaded": True,
        }
    for property_definition in re.finditer(PROPERTY_REGEX, class_body):
        property_name = property_definition.group("property_name")
        property_ptr = property_definition.group("property_ptr")
        properties[property_name] = property_ptr
    return {
        "type": "class",
        "reference": class_name,
        "lua_name": lua_name,
        "methods": methods,
        "properties": properties,
    }


def parse_lua_method_wrapper(wrapper_definition):
    wrapper_name = wrapper_definition.group("wrapper_name")
    wrapped_class = wrapper_definition.group("wrapped_class")
    wrapped_method = wrapper_definition.group("wrapped_method")
    min_args = wrapper_definition.group("min_args")
    max_args = wrapper_definition.group("max_args")
    return {
        "type": "wrapper",
        "wrapper_name": wrapper_name,
        "wrapped_class": wrapped_class,
        "wrapped_method": wrapped_method,
        "min_args": int(min_args),
        "max_args": int(max_args),
    }


def parse_lua_lambda_binding(lambda_definition):
    lambda_path = lambda_definition.group("lambda_path")
    lua_name = path_to_lua_name(lambda_path)

    return {"type": "lambda", "lua_name": lua_name}


def parse_lua_file_binding(binding_src):
    classes = []
    method_wrappers = []
    lambdas = []
    functions = []
    variables = []
    for class_definition in re.finditer(CLASS_REGEX, binding_src):
        classes.append(parse_lua_class_binding(class_definition))
    # for method_wrapper_definition in re.finditer(MEMBER_FUNCTION_OVERLOADS_REGEX, binding_src):
    #    method_wrappers.append(parse_lua_method_wrapper(method_wrapper_definition))
    # for lambda_definition in re.finditer(LAMBDA_REGEX, binding_src):
    #    lambdas.append(parse_lua_lambda_binding(lambda_definition))
    for function_definition in re.finditer(FUNCTION_REGEX, binding_src):
        functions.append(parse_lua_function_binding(function_definition))
    for variable_definition in re.finditer(VARIABLE_REGEX, binding_src):
        variables.append(parse_lua_variable_binding(variable_definition))
    return {
        "classes": classes,
        "method_wrappers": method_wrappers,
        "lambdas": lambdas,
        "functions": functions,
        "variables": variables,
    }


def parse_all_lua_bindings(bindings_directories, lua_db):
    lua_binding_tree = {}
    bindings_per_file = {}
    for bindings_directory in bindings_directories:
        for current_dir, _, files in os.walk(bindings_directory):
            for filepath in files:
                current_file = os.path.join(current_dir, filepath)
                with open(current_file) as binding_file:
                    bindings_per_file[current_file] = parse_lua_file_binding(
                        binding_file.read()
                    )
    for binding_file, binding_content in bindings_per_file.items():
        for class_content in binding_content["classes"]:
            insert_path_to_dict(
                lua_db.classes, class_content["lua_name"], class_content
            )
        for function_content in binding_content["functions"]:
            insert_path_to_dict(
                lua_db.functions, function_content["lua_name"], function_content
            )
        for lambda_content in binding_content["lambdas"]:
            insert_path_to_dict(
                lua_db.functions, lambda_content["lua_name"], lambda_content
            )
        for variable_content in binding_content["variables"]:
            insert_path_to_dict(
                lua_db.variables, variable_content["lua_name"], variable_content
            )
    return lua_binding_tree
