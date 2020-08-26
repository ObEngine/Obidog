<%namespace name="function_template" file="lua_function.mako"/>
<%namespace name="enum_template" file="lua_enum.mako"/>
<%namespace name="global_template" file="lua_global.mako"/>
<%namespace name="typedef_template" file="lua_typedef.mako"/>
<%def name="lua_namespace(namespace)">
<h1 class="title is-1"><i class="fas fa-folder-open"></i><span class="has-text-info"> namespace </span>${namespace.name}</h1>
<div class="divider is-left is-info">Info</div>
<div class="panel" id="doc_${namespace.name}">
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fas fa-cog" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">C++ name</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <p>${namespace.path}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fas fa-moon" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Lua name</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <p>${".".join(namespace.path.split("::"))}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fas fa-book" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Description</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <p>${namespace.description}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<div class="divider is-left is-info">Children</div>
% if namespace.namespaces:
<nav class="panel">
    <p class="panel-heading">
        Namespaces
    </p>
    % for namespace_value in namespace.namespaces.values():
        <a class="panel-block" href="${namespace_value.name}/index.html">
            <span class="panel-icon">
            <i class="fas fa-folder" aria-hidden="true"></i>
            </span>
            ${namespace_value.name}
        </a>
    % endfor
</nav>
% endif
% if namespace.classes:
<nav class="panel">
    <p class="panel-heading">
        Classes
    </p>
    % for class_value in namespace.classes.values():
        <a class="panel-block" href="${class_value.name}.html">
            <span class="panel-icon">
            <i class="fas fa-layer-group" aria-hidden="true"></i>
            </span>
            ${class_value.name}
        </a>
    % endfor
</nav>
% endif
% if namespace.enums:
<div class="divider is-left is-info">Enums</div>
% for enum in namespace.enums.values():
    ${enum_template.lua_enum(enum)}
% endfor
% endif
% if namespace.functions:
<div class="divider is-left is-info">Functions</div>
% for function in namespace.functions.values():
    % if function._type == "overload":
        <div class="divider is-left is-info">${function.name}</div>
        % for overload in function.overloads:
            ${function_template.lua_function(overload)}
        % endfor
        <div class="divider is-left is-info"></div>
    % else:
        ${function_template.lua_function(function)}
    % endif
% endfor
% endif
% if namespace.typedefs:
<div class="divider is-left is-info">Types</div>
% for typedef in namespace.typedefs.values():
    ${typedef_template.lua_typedef(typedef)}
% endfor
% endif
% if namespace.globals:
<div class="divider is-left is-info">Variables</div>
% for glob in namespace.globals.values():
    ${global_template.lua_global(glob)}
% endfor
% endif
</%def>