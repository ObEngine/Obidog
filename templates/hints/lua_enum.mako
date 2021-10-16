<%namespace name="utils" file="utils.mako"/>\
<%def name="lua_enum(enum)">
% if enum.description:
--- ${enum.description.strip().replace("\n", " ")}
---
% endif
---@class ${utils.merge_namespace_typename(enum.namespace, enum.name)}
${enum.namespace.replace("::", ".")}.${enum.name} = {
% for i, enum_value in enumerate(enum.values):
    ${enum_value.name} = ${i},
% endfor
};
</%def>