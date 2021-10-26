from dataclasses import dataclass, field
from typing import List, Optional

from obidog.models.functions import FunctionModel, ParameterModel


@dataclass
class BindableFunctionModel(FunctionModel):
    fqn: Optional[str] = None
    function_call: Optional[str] = None
    prefix_call_args: Optional[List[ParameterModel]] = field(default_factory=list)
    postfix_call_args: Optional[List[ParameterModel]] = field(default_factory=list)
    call_prefix: Optional[str] = None
    call_suffix: Optional[str] = None
    requires_static_cast: bool = False
    requires_call_wrapper: bool = False


BindingsSourceCode = str
