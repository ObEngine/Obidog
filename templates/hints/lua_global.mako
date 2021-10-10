<%def name="lua_global(glob)">
---@type global_type
${glob.namespace.replace("::", ".")}.${glob.name} = {};\
</%def>\