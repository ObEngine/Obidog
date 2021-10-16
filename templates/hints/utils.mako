<%def name="merge_namespace_typename(namespace, typename)">\
${".".join(([elem for elem in namespace.split("::") if elem] + [typename]))}\
</%def>\