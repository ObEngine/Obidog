<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ÖbEngine Lua Documentation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.0/css/bulma.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.1/js/all.min.js"
        integrity="sha512-M+hXwltZ3+0nFQJiVke7pqXY7VdtWW2jVG31zrml+eteTP7im25FdwtLhIBTWkaHRQyPrhO2uy8glLMHZzhFog=="
        crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.1/css/all.min.css"
        integrity="sha512-xA6Hp6oezhjd6LiLZynuukm80f8BoZ3OpcEYaqKoCV3HKQDrYjDE1Gu8ocxgxoXmwmSzM4iqPvCsOkQNiu41GA=="
        crossorigin="anonymous" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js"
        integrity="sha512-lnOllyZZlRk/gQIyjS3+h+LUy54uyM4aGq2zbGc82KTvBlp/fodSpdh/pywPztpU9zUqHcJr+jP+a1zLa9oCJw=="
        crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/fuse.js/dist/fuse.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/vs2015.min.css"
        integrity="sha512-w8aclkBlN3Ha08SMwFKXFJqhSUx2qlvTBFLLelF8sm4xQnlg64qmGB/A6pBIKy0W8Bo51yDMDtQiPLNRq1WMcQ=="
        crossorigin="anonymous" />
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
    <link href="https://jenil.github.io/bulmaswatch/darkly/bulmaswatch.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@creativebulma/bulma-divider@1.1.0/dist/bulma-divider.min.css" rel="stylesheet">
    <style>
        pre>code {
            font-family: "Fira Code", monospace;
        }

        .eggplant-header {
            background-color: #640080;
            color: white;
            border-top-right-radius: 2em;
        }

        
        .crimson-header {
            background-color: #6A0009;
            color: white;
            border-top-right-radius: 2em;
        }

        .gold-header {
            background-color: #7d6343;
            color: white;
            border-top-right-radius: 2em;
        }

        .ocean-header {
            background-color: #224382;
            color: white;
            border-top-right-radius: 2em;
        }

        .dark-panel {
            background-color: #222;
            color: white;
        }

        .transparent {
            background-color: transparent;
        }

        .eggplant-outline {
            border-color: #640080;
            border-radius: 4px;
            border-style: solid;
        }

        .crimson-outline {
            border-color: #6A0009;
            border-radius: 4px;
            border-style: solid;
        }

        .gold-outline {
            border-color: #7d6343;
            border-radius: 4px;
            border-style: solid;
        }

        .ocean-outline {
            border-color: #224382;
            border-radius: 4px;
            border-style: solid;
        }

        .header-padding
        {
            padding-left: 0.6em;
            padding-right: 0px;
            padding-top: 1em;
            padding-bottom: 0.5em;
        }

        .container
        {
            padding-top: 1em;
            padding-bottom: 1em;
        }

        .navbar
        {
            background-color: #640080;
        }

        .panel-block {
            padding: 0.8em 0.8em;
        }

        @font-face
        {
            font-family: "cyberfunk";
            src: url("https://obengine.io/Cyberfunk.ttf");
        }

        .brand-title
        {
            font-family: "cyberfunk";
        }
    </style>
    <script>hljs.initHighlightingOnLoad();</script>
    <script>
        let search_db;
        let fuse;
        fetch("https://${DB_LOCATION}").then(
            (resp) => resp.json()
        ).then(
            function(data) { search_db = data;}
        ).then(
            function() {
                fuse = new Fuse(search_db, {
                    keys: ['name'],
                    threshold: 0.3,
                    includeScore: true
                });
            }
        )
        </script>
</head>

<%namespace name="header_template" file="header.mako"/>
<%namespace name="class_template" file="lua_class.mako"/>
<%namespace name="function_template" file="lua_function.mako"/>
<%namespace name="namespace_template" file="lua_namespace.mako"/>
<body>
    ${header_template.header(CURRENT_VERSION)}
    <section class="container">
        % if target._type == "class":
            ${class_template.lua_class(target)}
        % elif target._type == "function":
            ${function_template.lua_function(target)}
        %elif target._type == "namespace":
            ${namespace_template.lua_namespace(target)}
        % endif
    </section>
</body>

</html>