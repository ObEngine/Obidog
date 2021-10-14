<%def name="lua_global(glob)">
---@type ${glob.type.type}
${glob.namespace.replace("::", ".")}.${glob.name} = {};\
</%def>\