<%def name="link_with_icon(text, url, icon)">
<div class="column is-1">
    <span>
        <i class="${icon}" aria-hidden="true"></i>
        <span class="has-text-info is-size-6"><a href="${url}">${text}</a></span>
    </span>
</div>
</%def>

<%def name="doc_link(type)">
% if type.startswith("obe") or type.startswith("vili"):
https://obengine.io/doc/lua/${'/'.join(type.split('.'))}.html
% elif type == "table":
https://www.lua.org/manual/5.4/manual.html#6.6
% elif type == "string":
https://www.lua.org/manual/5.4/manual.html#6.4
% else:
#
% endif
</%def>

<%def name="lua_function(function)">
<div class="panel" id="doc_${function.name}">
    <div class="panel-heading transparent header-padding">
        <div class="columns">
            <div class="column is-4 eggplant-header">
                <span>
                    <i class="fas fa-code" aria-hidden="true"></i>
                    <span class="title">${function.name}</span>
                </span>
            </div>
            % if function.urls.doxygen:
                ${link_with_icon(text="Doxygen", url=function.urls.doxygen, icon="fas fa-link")}
            % endif
            % if function.urls.source:
                ${link_with_icon(text="Source", url=function.urls.source, icon="fas fa-link")}
            % endif
            % if function.urls.bindings:
                ${link_with_icon(text="Bindings", url=function.urls.bindings, icon="fas fa-link")}
            % endif
        </div>
    </div>
    <div class="eggplant-outline">
        <div class="panel-block">
            <div class="tile is-ancestor pl-4 py-2">
                <div class="tile is-vertical">
                    <div class="tile">
                        <span>
                            <i class="fas fa-code" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Signature</h5>
                    </div>
                    <div class="tile pl-4 is-vertical">
                        <div class="tile pl-4">
                            <pre
                class="px-0 py-0"><code class="lua">${function.definition}</code></pre>
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
                            <p>${function.description}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        % if function.parameters:
        <div class="panel-block">
            <div class="tile is-ancestor pl-4 py-2">
                <div class="tile is-vertical">
                    <div class="tile">
                        <span>
                            <i class="fas fa-cube" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Parameters</h5>
                    </div>
                    % for parameter in function.parameters:
                    <div class="tile pl-4 is-vertical">
                        <div class="tile pl-4">
                            <p><a href="${doc_link(parameter.type.type)}" class="has-text-info">${parameter.type}</a> ${parameter.name}</p>
                        </div>
                        <div class="tile pl-6">
                            <p>${parameter.description}</p>
                        </div>
                    </div>
                    % endfor
                </div>
            </div>
        </div>
        % endif
        <div class="panel-block">
            <div class="tile is-ancestor pl-4 py-2">
                <div class="tile is-vertical">
                    <div class="tile">
                        <span>
                            <i class="fas fa-share" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Returns</h5>
                    </div>
                    <div class="tile pl-4">
                        <a href="${doc_link(function.return_type.type)}" class="pl-4"><b class="has-text-info">${function.return_type}</b></a>
                    </div>
                </div>
            </div>
        </div>
        % if function.urls.example:
        <div class="panel-block">
            <div class="tile is-ancestor pl-4 py-2">
                <div class="tile is-vertical">
                    <div class="tile">
                        <span>
                            <i class="fas fa-vial" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Example</h5>
                    </div>
                    <div class="tile pl-4">
                        <pre class="px-0 py-0"><code class="lua">${function.example}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        % endif
    </div>
</div>
</%def>