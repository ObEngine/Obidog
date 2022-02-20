<%namespace name="utils" file="utils.mako"/>\
<%def name="render(element)">
---@type ${element.type.type}
${utils.merge_namespace_typename(element.namespace, element.name)} = {};
</%def>