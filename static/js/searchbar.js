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
    a.href = element.url;
    a.classList.add("dropdown-item");
    a.classList.add("tile");

    var span = document.createElement("span");

    var i = document.createElement("i");
    i.classList.add("fas");

    if (element._type == "namespace") {
        i.classList.add("fa-folder")
    }
    else if (element._type == "class") {
        i.classList.add("fa-layer-group")
    }
    else if (element._type == "function") {
        i.classList.add("fa-code")
    }
    else if (element._type == "method") {
        i.classList.add("fa-code")
    }
    else if (element._type == "enum") {
        i.classList.add("fa-list-ol")
    }
    else if (element._type == "typedef") {
        i.classList.add("fa-flask")
    }
    else if (element._type == "global") {
        i.classList.add("fa-thermometer-half")
    }
    i.setAttribute("aria-hidden", true);

    var p = document.createElement("p");
    p.classList.add("pl-2");
    if (element._type == "method") {
        var class_name = element.from_class.split("::").slice(-1)[0];
        p.innerHTML = "<span style=\"color: grey\">" + class_name + "</span>." + element.name;
    }
    else {
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
    if (event.relatedTarget && event.relatedTarget.parentElement.id != "search-results") {
        search_bar.classList.remove("is-active");
    }
});

search_input.onkeypress = (event) => {
    search_results.innerHTML = "";
    let results = fuse.search(search_input.value, { "limit": 20 });
    for (result of results) {
        addSuggestion(result.item);
    }
};
