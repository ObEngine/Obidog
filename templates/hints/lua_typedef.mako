<%namespace name="utils" file="utils.mako"/>\
<%def name="lua_typedef(typedef)">
---@alias ${utils.merge_namespace_typename(typedef.namespace, typedef.name)} ${typedef.type}
</%def>
