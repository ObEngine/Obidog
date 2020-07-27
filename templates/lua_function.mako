<%def name="link_with_icon(text, url, icon)">
<div class="column is-1">
    <span>
        <i class="${icon}" aria-hidden="true"></i>
        <span class="has-text-info is-size-6"><a href="${url}">${text}</a></span>
    </span>
</div>
</%def>

<%def name="lua_function(function)">
<div class="panel">
    <div class="panel-heading transparent header-padding">
        <div class="columns">
            <div class="column is-4 eggplant-header">
                <span>
                    <i class="fas fa-chevron-circle-right" aria-hidden="true"></i>
                    <span class="title">${function.name}</span>
                </span>
            </div>
            ${link_with_icon(text="Doxygen", url=function.doxygen_url, icon="fas fa-link")}
            ${link_with_icon(text="Code", url=function.source_url, icon="fas fa-link")}
            ${link_with_icon(text="Bindings", url=function.bindings_url, icon="fas fa-link")}
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
                class="px-0 py-0"><code class="lua">${function.signature}</code></pre>
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
                            <p><b class="has-text-info">${parameter.type}</b> ${parameter.name}</p>
                        </div>
                        <div class="tile pl-6">
                            <p>${parameter.description}</p>
                        </div>
                    </div>
                    % endfor
                </div>
            </div>
        </div>
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
                        <p class="pl-4"><b class="has-text-info">${function.return_type}</b></p>
                    </div>
                </div>
            </div>
        </div>
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
    </div>
</div>
</%def>