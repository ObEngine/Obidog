from pydantic import Field

from obidog.models.functions import FunctionModel, ParameterModel


class BindableFunctionModel(FunctionModel):
    fqn: str | None = None
    function_call: str | None = None
    prefix_call_args: list[ParameterModel] | None = Field(default_factory=list)
    postfix_call_args: list[ParameterModel] | None = Field(default_factory=list)
    call_prefix: str | None = None
    call_suffix: str | None = None
    requires_static_cast: bool = False
    requires_call_wrapper: bool = False


BindingsSourceCode = str
