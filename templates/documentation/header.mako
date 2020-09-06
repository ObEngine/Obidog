<%def name="header(version)">
<nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
        <a class="navbar-item" href="https://obengine.io/doc/lua/index.html">
            <img src="https://obengine.io/doc/lua/logo.png" style="margin-right: 1em">
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
    (function() {
        let dropdown = document.querySelector('.dropdown');
        dropdown.addEventListener('click', function(event) {
            event.stopPropagation();
            dropdown.classList.toggle('is-active');
        });
    })();
    let search_bar = document.getElementById("search-bar");
    let search_input = document.getElementById("search-input");
    let search_results = document.getElementById("search-results");

    function addSuggestion(element) {
        console.log(element);
        var a = document.createElement("a");
        a.onmouseenter = () => {
            a.classList.add("is-active");
        };
        a.onmouseleave = () => {
            a.classList.remove("is-active");
        };
        a.href = element.urls.documentation;
        a.classList.add("dropdown-item");
        a.classList.add("tile");

        var span = document.createElement("span");
        
        var i = document.createElement("i");
        i.classList.add("fas");

        if (element._type == "namespace")
        {
            i.classList.add("fa-folder")
        }
        else if (element._type == "class")
        {
            i.classList.add("fa-layer-group")
        }
        else if (element._type == "function")
        {
            i.classList.add("fa-code")
        }
        else if (element._type == "method")
        {
            i.classList.add("fa-code")
        }
        else if (element._type == "enum")
        {
            i.classList.add("fa-list-ol")
        }
        else if (element._type == "typedef")
        {
            i.classList.add("fa-flask")
        }
        else if (element._type == "global")
        {
            i.classList.add("fa-thermometer-half")
        }
        i.setAttribute("aria-hidden", true);

        var p = document.createElement("p");
        p.classList.add("pl-2");
        if (element._type == "method")
        {
            var class_name = element.from_class.split("::").slice(-1)[0];
            p.innerHTML = "<span style=\"color: grey\">" + class_name + "</span>." + element.name;
        }
        else
        {
            p.innerHTML = element.name;
        }
        var lua_namespace = element.namespace.split("::").join(".");
        p.innerHTML += "<span class=\"is-size-7\" style=\"color: rgb(80, 80, 80)\"> (" + lua_namespace + ")</span>"

        span.appendChild(i);
        a.appendChild(span);
        a.appendChild(p);
        search_results.appendChild(a)
    }

    search_input.addEventListener('focus', (event) => {
        search_bar.classList.add("is-active");
    });

    search_input.addEventListener('blur', (event) => {
        if (event.relatedTarget && event.relatedTarget.parentElement.id != "search-results")
        {
            search_bar.classList.remove("is-active");
        }
    });

    search_input.onkeydown = (event) => {
        search_results.innerHTML = "";
        let results = fuse.search(search_input.value, {"limit": 20});
        for (result of results) {
            addSuggestion(result.item);
        }
    };
</script>
</%def>