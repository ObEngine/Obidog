# Obeldog

ÖbEngine's Lua Documentation Generator (work in progress)

**[ÖbEngine repository](https://github.com/Sygmei/ObEngine)**

Obeldog has two uses :
- Generating ÖbEngine bindings
- Generating ÖbEngine documentation

## Requirements

Obeldog has the following requirements :
- Python > 3.6 (+ install the Obeldog package using `pip install -e .` if you cloned this repository)
    - lxml
    - GitPython
- Doxygen (needs to be in `PATH`)
- Git (optional, see [below](#cloning-repository))

### Cloning repository

To make the script run faster, you should export the following environment variable : `OBENGINE_GIT_DIRECTORY`, if you don't export it though, it's fine, Obeldog will clone the repository in a temporary folder (it requires you to have `git` in `PATH`).

## Bindings generator

### Introduction

ÖbEngine embeds scripting languages to allow the user to create games with more flexibility and safety (it only supports Lua as of today).

Embedding a scripting language inside a C++ application is not free though, as C++ lacks any kind of reflection capability, it requires the user to manually bind each function/class/enum/... to the scripting language's virtual machine.

Doing such a task takes a lot of time, is error-prone and is really boring.
That's where Obeldog comes into action ! It will Doxygen as a reflection tool (it uses Doxygen's XML output) and automatically generates all the execution gluecode.

### Usage

Just run `obeldog bindings` and it will generate all the ÖbEngine bindings into the `output/` folder.
The output will have the following structure :
```
output/
    include/
        Bindings/
            Namespace1/
                ClassHuman.hpp
            Namespace2/
                ClassPerson.hpp
            ...
            NamespaceN/
    src/
        Bindings/
            Namespace1/
                ClassHuman.cpp
            Namespace2/
                ClassPerson.cpp
            ...
            NamespaceN/
```

### Flavours

The Obeldog bindings generator currently supports two flavours
- sol3 (wip)
- kaguya (deprecated)

New flavours can be added easily in the `obeldog/generators/bindings_flavours` folder.
It will maybe support the following flavours in the future when ÖbEngine is mature enough.
- Wrenpp
- GuraX
- Chaiscript
- pybind11

## Documentation generator

### Introduction

ÖbEngine C++ code is already documented using Doxygen's notation (documentation in comment).

Doxygen parses these comments and generate a fully fledged documentation website from it.

This is really practical from the user's point of view as any user can explore the codebase quickly, check-out which function exists, what kind of types a function takes as parameters, get more information about what a function does and get examples on how to use it.

All of that is great, but there is a catch: if the user uses the scripting language, it is not C++ anymore and therefore, the user won't be able to use the C++ documentation anymore (not the same symbols / types).

That's where Obeldog comes into action (again!), it will create try to generate a documentation for the target scripting language using the Doxygen XML and the generated bindings, translating symbols and types on the go to generate a coherant and nice looking documentation website.

### Usage

Just run `obeldog documentation` and it will generate all the ÖbEngine documentation into the `docs/` folder.

### Template customisation

(WIP)

## Extra informations

*The project might be renamed to Obidog (Öbengine BIndings & DOcumentation Generator) so the logo could be a mix of Obi-wan Kenobi, an eggplant and a dog*