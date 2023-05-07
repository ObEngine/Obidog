<%namespace name="utils" file="utils.mako"/>\
<%def name="render(element)">
% if element.description:
--- ${element.description.strip().replace("\n", " ")}
---
% endif
---@class ${utils.merge_namespace_typename(element.namespace, element.name)}
${element.namespace.replace("::", ".")}.${element.name} = {
% for i, enum_value in enumerate(element.values):
    ---@type ${utils.merge_namespace_typename(element.namespace, element.name)}
    ${enum_value.name} = ${i},
% endfor
};
</%def>