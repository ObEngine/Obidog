<%namespace name="function_template" file="lua_function.mako"/>\
<%namespace name="utils" file="utils.mako"/>\
<%def name="lua_class(klass)">\
---@class ${utils.merge_namespace_typename(klass.namespace, klass.name)}\
${' : ' if klass.bases and any([("<" not in base.type) for base in klass.bases]) else ''}\
${', '.join([base.type for base in klass.bases if "<" not in base.type]) if klass.bases else ''}
% for attribute in klass.attributes.values():
---@field ${attribute.name} ${attribute.type.type} #${attribute.description.strip().replace("\n", " ") if attribute.description else ''}
% endfor
${utils.merge_namespace_typename(klass.namespace, f"_{klass.name}")} = {};

% for constructor in klass.constructors:
${function_template.lua_function(constructor)}\
% endfor

% for method in klass.methods.values():
% if method._type == "function":
${function_template.lua_function(method)}\
% endif
% endfor

</%def>