<%namespace name="function_template" file="lua_function.mako"/>\
<%namespace name="utils" file="utils.mako"/>\
<%def name="render(element)">\
---@class ${utils.merge_namespace_typename(element.namespace, element.name)}\
${' : ' if element.bases and any([("<" not in base.type) for base in element.bases]) else ''}\
${', '.join([base.type for base in element.bases if "<" not in base.type]) if element.bases else ''}
% for attribute in element.attributes.values():
---@field ${attribute.name} ${attribute.type.type} #${attribute.description.strip().replace("\n", " ") if attribute.description else ''}
% endfor
${utils.merge_namespace_typename(element.namespace, f"_{element.name}")} = {};

% for constructor in element.constructors:
${function_template.render(constructor)}\
% endfor

% for method in element.methods.values():
% if method._type == "function":
${function_template.render(method)}\
% endif
% endfor

</%def>