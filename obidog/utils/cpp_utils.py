from typing import Optional


def make_fqn(
    name: str,
    namespace: Optional[str] = None,
    from_class: Optional[str] = None,
    sep: str = "::",
):
    elements = [element for element in [namespace, from_class, name] if element]
    return sep.join(elements)
