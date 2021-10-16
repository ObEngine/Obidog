<%namespace name="utils" file="utils.mako"/>\
<%def name="lua_global(glob)">
---@type ${glob.type.type}
${utils.merge_namespace_typename(glob.namespace, glob.name)} = {};
</%def>