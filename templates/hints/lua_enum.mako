<%def name="lua_enum(enum)">
% if enum.description:
--- ${enum.description.strip().replace("\n", " ")}
---
% endif
---@class ${enum.namespace.replace("::", ".")}.${enum.name}
${enum.namespace.replace("::", ".")}.${enum.name} = {
% for i, enum_value in enumerate(enum.values):
    ${enum_value.name} = ${i},
% endfor
};\
</%def>\