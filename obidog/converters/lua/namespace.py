from collections import defaultdict

from obidog.databases import CppDatabase

from obidog.models.namespace import NamespaceModel


def group_bindings_by_namespace(cpp_db: CppDatabase):
    group_by_namespace = defaultdict(NamespaceModel)
    for item_type in [
        "classes",
        "enums",
        "functions",
        "globals",
        "typedefs",
    ]:
        for item_name, item_value in getattr(cpp_db, item_type).items():
            strip_template = item_name.split("<")[0]
            last_namespace = "::".join(strip_template.split("::")[:-1:])
            if last_namespace in cpp_db.namespaces:
                getattr(group_by_namespace[last_namespace], item_type)[
                    item_name
                ] = item_value
    for namespace_name, namespace in group_by_namespace.items():
        namespace.name = namespace_name.split("::")[-1]
        namespace.path = namespace_name
        namespace.namespaces = {
            sub_namespace_name: sub_namespace
            for sub_namespace_name, sub_namespace in group_by_namespace.items()
            if "::".join(sub_namespace_name.split("::")[:-1:]) == namespace.path
        }
    root_namespaces = {
        sub_namespace_name: sub_namespace
        for sub_namespace_name, sub_namespace in group_by_namespace.items()
        if not "::" in sub_namespace_name
    }
    group_by_namespace[""] = NamespaceModel(
        name="ÖbEngine",
        path="",
        description="ÖbEngine documentation",
        namespaces=root_namespaces,
    )
    return group_by_namespace
