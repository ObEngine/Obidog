<%def name="lua_enum(enum)">
<div class="panel" id="doc_${enum.name}">
    <div class="panel-heading transparent header-padding">
        <div class="columns">
            <div class="column is-4 ocean-header">
                <span>
                    <i class="fas fa-list-ol" aria-hidden="true"></i>
                    <span class="title">${enum.name}</span>
                </span>
            </div>
        </div>
    </div>
    <div class="ocean-outline">
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
                            <p>${enum.description}</p>
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
                            <i class="fas fa-table" aria-hidden="true"></i>
                        </span>
                        <h5 class="title is-5 pl-2">Values</h5>
                    </div>
                    <div class="tile pl-4">
                        <table class="table">
                            <thead>
                                <tr>
                                <th>Name</th>
                                <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                            % for enum_value in enum.values:
                                <tr>
                                <th>${enum_value.name}</th>
                                <td>${enum_value.description}</td>
                                </tr>
                            % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        % if enum.urls.example:
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
                        <pre class="px-0 py-0"><code class="lua">${enum.example}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        % endif
    </div>
</div>
</%def>