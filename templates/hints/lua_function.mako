<%def name="lua_function(function)">\
% if function.description:
--- ${function.description.strip().replace("\n", " ")}
---
% endif
% for parameter in function.parameters:
---@param ${parameter.name}${'?' if parameter.default else ''} ${parameter.type.type} #${parameter.description.strip().replace("\n", " ")}
% endfor
% if function.return_type and function.return_type.type != "nil":
---@return ${function.return_type.type}
% endif
function ${function.namespace.replace("::", ".")}.\
% if hasattr(function, "from_class") and function.from_class != function.name:
_${function.from_class}:\
% endif
${function.name}(${", ".join([parameter.name for parameter in function.parameters])}) end

</%def>