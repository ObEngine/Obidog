<%namespace name="function_template" file="lua_function.mako"/>
<%def name="lua_class(klass)">
<h1 class="title is-1"><i class="fas fa-layer-group"></i><span class="has-text-info"> class </span>${klass.name}</h1>
<div class="divider is-left is-info">Info</div>
<div class="panel">
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
                        <p>${klass.cpp_name}</p>
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
                        <p>${klass.lua_name}</p>
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
                        <p>${klass.description}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    % if klass.helper:
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fab fa-hire-a-helper" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Helper</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <p>${klass.helper}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    % endif
</div>
% if klass.attributes:
<div class="divider is-left is-info">Attributes</div>
% endif
% if klass.methods:
<div class="divider is-left is-info">Methods</div>
% for method in klass.methods:
    ${function_template.lua_function(method)}
% endfor
% endif
</%def>