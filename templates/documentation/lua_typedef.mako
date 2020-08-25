<%def name="lua_typedef(typedef)">
<div class="panel">
    <div class="panel-heading transparent header-padding">
        <div class="columns">
            <div class="column is-4 gold-header">
                <span>
                    <i class="fas fa-chevron-circle-right" aria-hidden="true"></i>
                    <span class="title">${typedef.name}</span>
                </span>
            </div>
        </div>
    </div>
    <div class="gold-outline">
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
                            <p>${typedef.description}</p>
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
                            <p>${typedef.type}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        % if typedef.urls.example:
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
                        <pre class="px-0 py-0"><code class="lua">${typedef.example}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        % endif
    </div>
</div>
</%def>