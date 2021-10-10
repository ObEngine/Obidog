<%namespace name="function_template" file="lua_function.mako"/>\
<%def name="lua_class(klass)">\
---@class ${klass.namespace.replace("::", ".")}.${klass.name}
% for attribute in klass.attributes.values():
---@field ${attribute.name} ${attribute.type} #${attribute.description.strip().replace("\n", " ")}
% endfor
${klass.namespace.replace("::", ".")}._${klass.name} = {};

% for constructor in klass.constructors:
${function_template.lua_function(constructor)}\
% endfor

% for method in klass.methods.values():
% if method._type == "function":
${function_template.lua_function(method)}\
% endif
% endfor

</%def>