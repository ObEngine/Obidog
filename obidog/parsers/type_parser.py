from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.utils.xml_utils import get_content


def parse_real_type(element, doxygen_index):
    if element.find("type").find("ref") is not None:
        param_refs = element.find("type").findall("ref")
        final_type = list(element.find("type").itertext())
        for param_ref in param_refs:
            param_refid = param_ref.attrib.get("refid")
            if param_refid:
                real_ref_type = doxygen_index[param_refid]["full_name"]
            else:
                real_ref_type = doxygen_refid_to_cpp_name(param_ref)
            repl_index = final_type.index(get_content(param_ref))
            final_type[repl_index] = real_ref_type
        return "".join(final_type).strip()
    else:
        return get_content(element.find("type")).strip()


# TODO: remove this ? (replace with split_unembedded)
def split_root_types(templated_type: str):
    inner_template_count = 0
    segments = []
    buffer = ""
    for char in templated_type:
        if char in ["<", "("]:
            inner_template_count += 1
            buffer = buffer + char
        elif char in [">", ")"]:
            inner_template_count -= 1
            buffer = buffer + char
        elif char == "," and not inner_template_count:
            segments.append(buffer.strip())
            buffer = ""
        else:
            buffer = buffer + char
    if buffer.strip():
        segments.append(buffer.strip())
    return [segment.strip() for segment in segments]


TEMPLATE_AND_FUNCTION_TYPE_EMBED_SYMBOLS = [("<", ">"), ("(", ")")]


def split_unembedded(string: str, sep: str, embed_symbols: List[Tuple[str, str]]):
    stack = []
    segments = []
    buffer = ""
    opening_symbols = [sym[0] for sym in embed_symbols]
    closing_symbols = [sym[1] for sym in embed_symbols]
    for char in string:
        if char in opening_symbols:
            stack.append(char)
            buffer = buffer + char
        elif char in closing_symbols:
            if opening_symbols.index(stack[-1]) != closing_symbols.index(char):
                raise RuntimeError("unbalanced opening / closing symbols")
            stack.pop(len(stack) - 1)
            buffer = buffer + char
        elif char == sep and not stack:
            segments.append(buffer.strip())
            buffer = ""
        else:
            buffer = buffer + char
    if buffer.strip():
        segments.append(buffer.strip())
    return [segment.strip() for segment in segments]


class CppQualifiers:
    def __init__(self, prefix_qualifiers: List[str], postfix_qualifiers: List[str]):
        self.prefix_qualifiers = prefix_qualifiers
        self.postfix_qualifiers = postfix_qualifiers

    def format(self, type: str):
        return " ".join(self.prefix_qualifiers + [type] + self.postfix_qualifiers)

    def is_const_ref(self):
        return (
            (self.prefix_qualifiers == ["const"] and self.postfix_qualifiers == ["&"])
            or self.postfix_qualifiers == ["const&"]
            or self.postfix_qualifiers == ["const", "&"]
        )


def strip_qualifiers(type: str) -> Tuple[str, CppQualifiers]:
    valid_prefix_qualifiers = ["const", "constexpr", "consteval", "static"]
    valid_postfix_qualifiers = ["&", "*", "const&", "const*", "const"]
    prefix_qualifiers = []
    postfix_qualifiers = []
    qualifier_detected = True
    while qualifier_detected:
        type = type.lstrip(" ")
        qualifier_detected = False
        for valid_prefix_qualifier in valid_prefix_qualifiers:
            if type.startswith(f"{valid_prefix_qualifier} "):
                type = type.removeprefix(f"{valid_prefix_qualifier} ")
                prefix_qualifiers.append(valid_prefix_qualifier)
                qualifier_detected = True
    qualifier_detected = True
    while qualifier_detected:
        type = type.rstrip(" ")
        qualifier_detected = False
        for valid_postfix_qualifier in valid_postfix_qualifiers:
            if type.endswith(f"{valid_postfix_qualifier}"):
                type = type.removesuffix(f"{valid_postfix_qualifier}")
                postfix_qualifiers.append(valid_postfix_qualifier)
                qualifier_detected = True
    return type, CppQualifiers(
        prefix_qualifiers=prefix_qualifiers, postfix_qualifiers=postfix_qualifiers
    )


class CppType(ABC):
    def __init__(self, qualifiers: CppQualifiers) -> None:
        super().__init__()
        self.qualifiers = qualifiers
        self.type: Optional[Union[str, CppType]] = None

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def traverse(self, func: callable):
        pass


class CppBaseType(CppType):
    def __init__(self, type: str, qualifiers: CppQualifiers) -> None:
        super().__init__(qualifiers)
        self.type = type

    def __str__(self) -> str:
        return self.qualifiers.format(str(self.type))

    def traverse(self, func: callable):
        self.type = func(self.type)


class CppTemplateType(CppType):
    def __init__(
        self,
        type: str,
        qualifiers: CppQualifiers,
        template_types: List["CppTemplateType"],
    ):
        super().__init__(qualifiers)
        self.type = type
        self.template_types = template_types

    def __str__(self):
        return self.qualifiers.format(
            f"{self.type}<"
            f"{', '.join([str(template_type) for template_type in self.template_types])}>"
        )

    def traverse(self, func: callable):
        self.type = func(self.type)
        for template_type in self.template_types:
            template_type.traverse(func)


class CppFunctionArg(CppType):
    def __init__(
        self, type: CppType, qualifiers: CppQualifiers, name: Optional[str] = None
    ):
        super().__init__(qualifiers)
        self.type = type
        self.name = name

    def __str__(self) -> str:
        if self.name:
            return self.qualifiers.format(f"{self.type} {self.name}")
        else:
            return self.qualifiers.format(str(self.type))

    def traverse(self, func: callable):
        self.type = func(self.type)


class CppFunctionType(CppType):
    def __init__(
        self,
        return_type: CppType,
        qualifiers: CppQualifiers,
        args: List[CppFunctionArg],
    ):
        super().__init__(qualifiers)
        self.type = return_type
        self.args = args

    def __str__(self) -> str:
        return self.qualifiers.format(
            f"{self.type}(" f"{', '.join([str(arg) for arg in self.args])})"
        )

    def traverse(self, func: callable):
        self.type = func(self.type)
        for arg in self.args:
            arg.traverse(func)


def parse_templated_type(templated_type: str) -> CppTemplateType:
    templated_type, qualifiers = strip_qualifiers(templated_type)
    roots = split_root_types(templated_type)
    if len(roots) > 1:
        return [parse_templated_type(root) for root in roots]
    else:
        root = roots[0]
        root_type = root.split("<")[0].strip()
        child_types = (
            "<".join(templated_type.split("<")[1::]).strip().removesuffix(">").strip()
        )
        return CppTemplateType(
            root_type,
            qualifiers,
            [
                parse_cpp_type(child_type)
                for child_type in split_root_types(child_types)
            ],
        )


def parse_function_type(function_type: str) -> CppFunctionType:
    function_type, qualifiers = strip_qualifiers(function_type)
    fun_return_type, fun_args = function_type.split("(")
    fun_return_type = parse_cpp_type(fun_return_type)
    fun_args = fun_args.strip().removesuffix(")").strip()
    fun_args = split_root_types(fun_args)
    fun_args_parsed = []
    for fun_arg in fun_args:
        fun_arg, fun_arg_qualifiers = strip_qualifiers(fun_arg)
        fun_arg_split = split_unembedded(
            fun_arg, " ", TEMPLATE_AND_FUNCTION_TYPE_EMBED_SYMBOLS
        )
        # Is the argument name present ?
        if len(fun_arg_split) == 2:
            fun_arg_type, fun_arg_name = fun_arg_split
            fun_arg_type = parse_cpp_type(fun_arg_type)
            fun_args_parsed.append(
                CppFunctionArg(fun_arg_type, fun_arg_qualifiers, fun_arg_name)
            )
        elif len(fun_arg_split) == 1:
            fun_arg_type = fun_arg_split[0]
            fun_arg_type = parse_cpp_type(fun_arg_type)
            fun_args_parsed.append(CppFunctionArg(fun_arg_type, fun_arg_qualifiers))
        else:
            raise RuntimeError("is that supposed to happen ?")

    return CppFunctionType(fun_return_type, qualifiers, fun_args_parsed)


def parse_cpp_type(cpp_type: str) -> CppType:
    if "<" not in cpp_type and "(" not in cpp_type:
        return CppBaseType(*strip_qualifiers(cpp_type))
    elif "<" not in cpp_type:
        return parse_function_type(cpp_type)
    elif "(" not in cpp_type:
        return parse_templated_type(cpp_type)
    elif cpp_type.strip().endswith(")"):
        return parse_function_type(cpp_type)
    elif cpp_type.index("<") < cpp_type.index("("):
        return parse_templated_type(cpp_type)
    elif cpp_type.index("(") < cpp_type.index("<"):
        return parse_function_type(cpp_type)
    raise RuntimeError("shouldn't reach this branch")


def patch_incomplete_type(parent: str, doxygen_index):
    def patch_incomplete_type_inner(incomplete_type: Union[str, CppType]):
        incomplete_type = (
            incomplete_type.type
            if isinstance(incomplete_type, CppType)
            else incomplete_type
        )
        parent_path = parent.split("::")
        if parent_path:
            for parent_path_using_length in range(len(parent_path), 0, -1):
                parent_path_segment = parent_path[0:parent_path_using_length]
                full_name_attempt = (
                    f"{'::'.join(parent_path_segment)}::{incomplete_type}"
                )
                if full_name_attempt in doxygen_index and doxygen_index[
                    full_name_attempt
                ]["kind"] in ["class", "typedef", "enum"]:
                    return full_name_attempt
        possible_types = []
        incomplete_type_segments = str(incomplete_type).split("::")
        for elem_name in doxygen_index:
            if (
                elem_name.split("::")[-len(incomplete_type_segments) : :]
                == incomplete_type_segments
            ):
                possible_types.append(elem_name)
        if not possible_types:
            return incomplete_type
        if len(possible_types) == 1:
            return possible_types[0]
        else:
            raise RuntimeError("conflict, multiple types detected")

        return incomplete_type

    return patch_incomplete_type_inner


def rebuild_incomplete_type(incomplete_type: str, parent: str, doxygen_index):
    # TODO: do that only once
    doxygen_index_using_full_name_as_key = {
        elem["full_name"]: elem for elem in doxygen_index.values()
    }
    parsed_type = parse_cpp_type(incomplete_type)
    parsed_type.traverse(
        patch_incomplete_type(parent, doxygen_index_using_full_name_as_key)
    )
    return str(parsed_type)
