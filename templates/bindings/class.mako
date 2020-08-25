<%def name="method_cast(method)">
static_cast<${method.return_type} (${method.class_name}::*)(${method.parameters}) ${method.qualifiers}>(${method.method_address})
</%def>

<%def name="method_default_values_lambda_wrapper(method)">
% if isinstance(method, FunctionPatchModel):
[](${method.parameters}) -> ${method.return_type} {{ return ${method.method_call}(${method.parameters_names}); }}
% else:
[](${method.parameters}) -> ${method.return_type} {{ return self->${method.method_call}(${method.parameters_names}); }}
% endif
</%def>