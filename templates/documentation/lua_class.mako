<%namespace name="function_template" file="lua_function.mako"/>
<%def name="lua_class(klass)">
<h1 class="title is-1"><i class="fas fa-layer-group"></i><span class="has-text-info"> class </span>${klass.name}</h1>
<div class="divider is-left is-info">Info</div>
<div class="panel" id="doc_${klass.name}">
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
                        <p>${klass.namespace}::${klass.name}</p>
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
                        <p>${".".join(klass.namespace.split("::"))}.${klass.name}</p>
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
    % if klass.flags.helpers:
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fab fa-hire-a-helper" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Helper</h5>
                </div>
                % for helper in klass.flags.helpers:
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <p>${helper}</p>
                    </div>
                </div>
                % endfor
            </div>
        </div>
    </div>
    % endif
</div>
% if any([klass.urls.doxygen, klass.urls.source, klass.urls.bindings]):
<div class="divider is-left is-info">URLs</div>
<div class="panel" id="urls_${klass.name}">
    % if klass.urls.doxygen:
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fas fa-book" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Doxygen</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <a href="${klass.urls.doxygen}">
                            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
                            <b>Go to Doxygen (${klass.namespace}::${klass.name})</b>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    % endif
    % if klass.urls.source:
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fab fa-github" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Source</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <a href="${klass.urls.source}">
                            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
                            <b>Go to source (${klass.namespace}::${klass.name})</b>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    % endif
    % if klass.urls.bindings:
    <div class="panel-block">
        <div class="tile is-ancestor pl-4 py-2">
            <div class="tile is-vertical">
                <div class="tile">
                    <span>
                        <i class="fas fa-compress-arrows-alt" aria-hidden="true"></i>
                    </span>
                    <h5 class="title is-5 pl-2">Bindings</h5>
                </div>
                <div class="tile pl-4 is-vertical">
                    <div class="tile pl-4">
                        <a href="${klass.urls.bindings}">
                            <i class="fas fa-external-link-alt" aria-hidden="true"></i>
                            <b>Go to bindings (${klass.namespace}::${klass.name})</b>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    % endif
</div>
% endif
% if klass.attributes:
<div class="divider is-left is-info">Attributes</div>
% endif
% if klass.methods:
<div class="divider is-left is-info">Methods</div>
% for method in klass.methods.values():
    % if method._type == "overload":
        <div class="divider is-left is-info">${method.name}</div>
        % for overload in method.overloads:
            ${function_template.lua_function(overload)}
        % endfor
        <div class="divider is-left is-info"></div>
    % else:
        ${function_template.lua_function(method)}
    % endif
% endfor
% endif
</%def>