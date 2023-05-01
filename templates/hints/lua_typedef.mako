<%namespace name="utils" file="utils.mako"/>\
<%def name="render(element)">
---@alias ${utils.merge_namespace_typename(element.namespace, element.name)} ${element.type}
</%def>
