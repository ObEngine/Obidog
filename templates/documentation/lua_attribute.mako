<%namespace name="utils" file="utils.mako"/>
<%def name="lua_attribute(attribute)">
<div class="panel" id="doc_${attribute.name}">
    <div class="panel-heading transparent header-padding">
        <div class="columns">
            <div class="column is-4 crimson-header">
                <span>
                    <i class="fas fa-tag" aria-hidden="true"></i>
                    <span class="title">${attribute.name}</span>
                </span>
            </div>
            % if attribute.urls.doxygen:
                ${utils.link_with_icon(text="Doxygen", url=attribute.urls.doxygen, icon="fas fa-link")}
            % endif
            % if attribute.urls.source:
                ${utils.link_with_icon(text="Source", url=attribute.urls.source, icon="fas fa-link")}
            % endif
            % if attribute.urls.bindings:
                ${utils.link_with_icon(text="Bindings", url=attribute.urls.bindings, icon="fas fa-link")}
            % endif
        </div>
    </div>
    <div class="crimson-outline">
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
                            <p>${attribute.description}</p>
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
                            <i class="fas fa-share" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Type</h5>
                    </div>
                    <div class="tile pl-4 is-vertical">
                        <div class="tile pl-4">
                            <p>${attribute.type}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        % if attribute.initializer:
        <div class="panel-block">
            <div class="tile is-ancestor pl-4 py-2">
                <div class="tile is-vertical">
                    <div class="tile">
                        <span>
                            <i class="fas fa-infinity" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Value</h5>
                    </div>
                    <div class="tile pl-4 is-vertical">
                        <div class="tile pl-4">
                            <p>${attribute.initializer}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        % endif
        % if attribute.urls.example:
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
                        <pre class="px-0 py-0"><code class="lua">${attribute.example}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        % endif
    </div>
</div>
</%def>