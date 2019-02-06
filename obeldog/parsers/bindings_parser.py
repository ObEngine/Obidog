import json
import os
import re

CLASS_REGEX = re.compile(r"""
\(\s*\*lua\s*\)\s*
(?P<class_path>\[\".+\"\])
\.setClass\(\s*kaguya::UserdataMetatable
<\s*(?P<class_name>([^,>])+)\s*(,\s*.+\s*)?>
\s*\(\s*\)(?P<class_body>[^;]*)\);
""".replace("\n", ""))

METHOD_REGEX = re.compile(r"""
\.addFunction\(\s*
\"(?P<method_name>[^\"]+)\"
,\s*(?P<method_funcptr>[^.]+)\)
""".replace("\n", ""))

OVERLOADED_METHOD_REGEX = re.compile(r"""
\.addOverloadedFunctions\(\s*
\"(?P<method_name>[^\"]+)\"
,\s*(?P<method_funcptrs>[^.]+)\)
""".replace("\n", ""))

PROPERTY_REGEX = re.compile(r"""
\.addProperty\(\s*
\"(?P<property_name>[^\"]+)\"
,\s*(?P<property_ptr>[^.]+)\)
""".replace("\n", ""))

MEMBER_FUNCTION_OVERLOADS_REGEX = re.compile(r"""
KAGUYA_MEMBER_FUNCTION_OVERLOADS\(\s*
(?P<wrapper_name>\w+)\s*
,\s*(?P<wrapped_class>[\w:]+)\s*
,\s*(?P<wrapped_method>[\w:]+)\s*
,\s*(?P<min_args>\d+),
\s*(?P<max_args>\d+)\s*\);
""".replace("\n", ""))

def insert_path_to_dict(tree, path, value):
    splitted_path = path.split(".")
    for i, path_part in enumerate(splitted_path):
        if i == len(splitted_path) - 1:
            tree[path_part] = value
            break
        elif not path_part in tree:
            tree[path_part] = {}
        tree = tree[path_part]

def classpath_to_lua_name(classpath):
    return classpath \
        .replace("\"][\"", ".") \
        .replace("[\"", "") \
        .replace("\"]", "")

def parse_lua_variable_binding(variable_binding_src):
    pass

def parse_lua_function_binding(function_binding_src):
    pass

def parse_lua_class_binding(class_definition):
    class_name = class_definition.group("class_name")
    class_path = class_definition.group("class_path")
    lua_name = classpath_to_lua_name(class_path)
    class_body = class_definition.group("class_body")
    print("  Found class definition", class_name, class_path, lua_name)
    methods = {}
    properties = {}
    for method_definition in re.finditer(METHOD_REGEX, class_body):
        method_name = method_definition.group("method_name")
        method_funcptr = method_definition.group("method_funcptr")
        print("    Found method definition", method_name, method_funcptr)
        methods[method_name] = {
            "name": method_name,
            "function_ptr": method_funcptr,
            "overloaded": False
        }
    for ov_method_definition in re.finditer(OVERLOADED_METHOD_REGEX, class_body):
        method_name = ov_method_definition.group("method_name")
        method_funcptrs = ov_method_definition.group("method_funcptrs")
        print("    Found overloaded-method definition", method_name, method_funcptrs)
        methods[method_name] = {
            "name": method_name,
            "function_ptr": method_funcptrs,
            "overloaded": True
        }
    for property_definition in re.finditer(PROPERTY_REGEX, class_body):
        property_name = property_definition.group("property_name")
        property_ptr = property_definition.group("property_ptr")
        print("    Found property definition", property_name, property_ptr)
        properties[property_name] = property_ptr
    return {
        "type": "class",
        "name": class_name,
        "lua_name": lua_name,
        "methods": methods,
        "properties": properties
    }

def parse_lua_method_wrapper(wrapper_definition):
    wrapper_name = wrapper_definition.group("wrapper_name")
    wrapped_class = wrapper_definition.group("wrapped_class")
    wrapped_method = wrapper_definition.group("wrapped_method")
    min_args = wrapper_definition.group("min_args")
    max_args = wrapper_definition.group("max_args")
    print(f"  Found method_wrapper {wrapper_name} for {wrapped_class}::{wrapped_method} [{min_args}:{max_args}]")
    return {
        "type": "wrapper",
        "wrapper_name": wrapper_name,
        "wrapped_class": wrapped_class,
        "wrapped_method": wrapped_method,
        "min_args": int(min_args),
        "max_args": int(max_args)
    }

def parse_lua_file_binding(binding_src):
    classes = []
    method_wrappers = []
    for class_definition in re.finditer(CLASS_REGEX, binding_src):
        classes.append(parse_lua_class_binding(class_definition))
    for method_wrapper_definition in re.finditer(MEMBER_FUNCTION_OVERLOADS_REGEX, binding_src):
        method_wrappers.append(parse_lua_method_wrapper(method_wrapper_definition))
    return {
        "classes": classes,
        "method_wrappers": method_wrappers
    }
        

def parse_all_lua_bindings(bindings_directories):
    lua_binding_tree = {}
    bindings_per_file = {}
    for bindings_directory in bindings_directories:
        for current_dir, _, files in os.walk(bindings_directory):
            for filepath in files:
                current_file = os.path.join(current_dir, filepath)
                print("Parsing file", current_file)
                with open(current_file) as binding_file:
                    bindings_per_file[current_file] = parse_lua_file_binding(binding_file.read())
    for binding_file, binding_content in bindings_per_file.items():
        for class_content in binding_content["classes"]:
            insert_path_to_dict(lua_binding_tree, class_content["lua_name"], class_content)
    print(json.dumps(lua_binding_tree, indent=4))
    """print(filepath)
    clname = ""
    for index, line in enumerate(lines):
        line = line.replace("\n", "")
        if ".setClass" in line:
            tline = line.replace(" ", "")
            luaname = tline.split(".setClass")[0].replace("(*lua)", "").replace("[\"", "").replace("\"]", ".")
            if luaname.endswith("."):
                luaname = luaname[:-1:]
            if not "//" in luaname and not "/*" in luaname:
                #print(tline.split(".setClass")[1])
                cppname = tline.split(".setClass")[1].split(",")[0].replace("(kaguya::UserdataMetatable<", "").replace(">()", "")
                print(luaname, cppname)
                classes[luaname] = {}
                classes[luaname]["luaname"] = luaname
                classes[luaname]["cppname"] = cppname
                clname = "obe::" + cppname
                doclink = ""
                if luaname in fillinks:
                    doclink = fillinks[luaname]
                else:
                    print("Warning: Can't find doc link for", luaname, cppname)
                classes[luaname]["doclink"] = doclink
                classes[luaname]["module"] = filepath.replace("Bindings.cpp", "")
                classes[luaname]["methods"] = {}
                cclass = luaname
        elif " .addFunction" in line:
            print(index, line)
            method = line.replace(" ", "").replace(".addFunction", "")
            fluaname, fcppname = method.split(",")[0], method.split(",")[1]
            fluaname = fluaname.replace("\"", "").replace("(", "")
            fcppname = fcppname.replace("\"", "").replace(")", "").replace("&", "")
            if fcppname.endswith("_wrapper("):
                print("Found wrapper form, simplifying")
                fcppname = fcppname.replace("_wrapper(", "")
                fcppname = fcppname.split("_")[0] + "::" + fcppname
                fcppname = fcppname.replace("_", "::")
            #print(luaname, "=>", cppname)
            methoddict = {}
            if clname in allclasses and fcppname.split("::")[-1] in allclasses[clname]["methods"]:
                methoddict = allclasses[clname]["methods"][fcppname.split("::")[-1]]
                print("Found methoddict for", luaname)
            else:
                print("############ Warning, could not find methoddict for", luaname)
            pprint(methoddict)
            methoddict["cppname"] = fcppname
            if cclass != "":
                classes[cclass]["methods"][fluaname] = methoddict
        elif "kaguya::function" in line:
            print("KAGUYA::FUNCTION =======================================================================>", index, line)
            fluaname = line.split("=")[0].replace("(*lua)", "")
            fluaname = [i.replace("[", "").replace("]", "").replace("\"", "") for i in fluaname.split("][")]
            fluaname, fromclass = ".".join(fluaname), ".".join(fluaname[0:-1])
            print("Found LUANAME : ", fluaname, "from class", fromclass)"""