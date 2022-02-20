<%def name="render(element)">\
% if element.description:
--- ${element.description.strip().replace("\n", " ")}
---
% endif
% for parameter in element.parameters:
---@param ${parameter.name}${'?' if parameter.default else ''} ${parameter.type.type} #${parameter.description.strip().replace("\n", " ")}
% endfor
% if element.return_type and element.return_type.type != "nil":
---@return ${element.return_type.type}
% endif
function ${element.namespace.replace("::", ".")}${'.' if element.namespace else ''}\
% if getattr(element, "from_class", False) and element.from_class != element.name:
_${element.from_class}:\
% endif
${element.name}(${", ".join([parameter.name for parameter in element.parameters])}) end

</%def>