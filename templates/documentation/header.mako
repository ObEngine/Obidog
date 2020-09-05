<%def name="header(WEBSITE_LOCATION, DOCUMENTATION_PATH, DB_LOCATION, version)">
<nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
        <a class="navbar-item" href="https://${WEBSITE_LOCATION}/${DOCUMENTATION_PATH}/index.html">
            <img src="https://${WEBSITE_LOCATION}/${DOCUMENTATION_PATH}/static/img/logo.png" style="margin-right: 1em">
            <h1 class="title brand-title">ObEngine</h1>
        </a>

        <a role="button" class="navbar-burger burger" aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
        </a>
    </div>

    <div id="navbarBasicExample" class="navbar-menu">
        <div class="navbar-start">
            <div class="navbar-item dropdown">
                <div class="dropdown-trigger">
                    <button class="button" aria-haspopup="true" aria-controls="dropdown-menu">
                    <span>${version}</span>
                    <span class="icon is-small">
                        <i class="fas fa-angle-down" aria-hidden="true"></i>
                    </span>
                    </button>
                </div>
                <div class="dropdown-menu" id="dropdown-menu" role="menu">
                    <div class="dropdown-content">
                    <a href="#" class="dropdown-item">
                        0.1
                    </a>
                    <a href="#" class="dropdown-item">
                        0.2
                    </a>
                    <a href="#" class="dropdown-item">
                        0.3
                    </a>
                    <a href="#" class="dropdown-item">
                        0.4
                    </a>
                    <a href="#" class="dropdown-item">
                        0.5
                    </a>
                    </div>
                </div>
            </div>
            <a class="navbar-item" href="https://github.com/Sygmei/ObEngine">
                GitHub
            </a>

            <div class="navbar-item has-dropdown is-hoverable">
                <a class="navbar-link">
                More
                </a>

                <div class="navbar-dropdown">
                <a class="navbar-item">
                    About
                </a>
                <a class="navbar-item">
                    Contact
                </a>
                <hr class="navbar-divider">
                <a class="navbar-item" href="https://github.com/ObEngine/Obidog/issues">
                    Report an issue
                </a>
                </div>
            </div>
        </div>

        <div class="navbar-end">
            <div class="navbar-item" style="width: 200%">
                <div class="field is-grouped" style="width: 200%">
                    <div class="dropdown" id="search-bar" style="width: 200%">
                        <div class="dropdown-trigger" style="width: 200%">
                            <div class="control has-icons-left">
                                <input type="text" placeholder="Search for element" class="input" id="search-input" style="width: 200%">
                                <span class="icon is-left">
                                    <i class="fa fa-search"></i>
                                </span>
                                </div>
                        </div>
                        <div class="dropdown-menu" id="dropdown-menu" role="menu">
                            <div class="dropdown-content" id="search-results">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</nav>
<script>
let search_db;
let fuse;
fetch("https://${DB_LOCATION}").then(
    (resp) => resp.json()
).then(
    function (data) { search_db = data; }
).then(
    function () {
        fuse = new Fuse(search_db, {
            keys: ['name'],
            threshold: 0.3,
            includeScore: true
        });
    }
)
</script>
<script src="https://${WEBSITE_LOCATION}/${DOCUMENTATION_PATH}/static/js/version_selector.js"></script>
<script src="https://${WEBSITE_LOCATION}/${DOCUMENTATION_PATH}/static/js/searchbar.js"></script>
</%def>