# Introduction

Muxkt is a wrapper for [SubKt](https://github.com/Myaamori/SubKt) that was written with the aim of sorting out the output of SubKt. While the output of SubKt is not bad, the important information can sometimes be hidden among a wall of text that is not entirely necessary to the end user to see. So this tool takes both the stdout and stderr of SubKt and presents in more digestable format. This began as a [bash script](https://github.com/PhosCity/muxsh) but I rewrote this in python for people who are in the environment where bash and GNU coreutils are not present in their system. I also wrote this to learn python and as such, the code may not be pleasant to look at.

## Main feature of muxkt

* It's config based where you can save any number of your current projects. You can thus run this script and choose from one of your projects to mux it's episodes.
* Choose a single or multiple episodes to mux then all at once.
* Pass the path of the project directly as an argument to mux episodes in that folder if it's not saved in your config.
* Sort both the stdout and stderr of SubKt and present them less verbosely.
* Make fatal errors more easier to see. (For example: The missing fonts are highlighted among the list of warnings.)
* Redo the last mux (single or mutiple episodes) with a flag.
* If you want to watch the original output of Subkt for the last mux you did, you can easily do so with a flag.
* Easily add or remove projects from the config. There is also a command to open the config in your default editor so that you can manually edit the config if you wish.
* Support for alternate folder structure. [Read more about alternate folder structure here.](#Alternate Folder Structure)

# Installation

```
git clone https://github.com/PhosCity/muxkt.git
cd muxkt
pip install .
```

# Usage
This project is made for following folder structure:
```
.
├── 01
├── 02
├── 03
├── ...
└── Subkt Configs
```

The help page for muxkt looks like this. It has commands just like git where the command after `muxkt` informs the program what it should do. Currently, the commands present are mux and config. Since you are most likely use mux comand a lot, I recommend you to alias `muxkt mux` to something like `mux` if you wish.

```
Usage: muxkt [OPTIONS] COMMAND [ARGS]...

  Wrapper for Subkt written in Python.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  config  Add, remove, edit projects in the config.
  mux     Mux the episodes.
```

The following output of `muxkt mux --help` should give you a pretty decent idea of what is available to you while muxing. However, you can always just run `muxkt mux` and the program will guide you to do everything interactively as well.
```
Usage: muxkt mux [OPTIONS]

  Mux the episodes.

Options:
  -p, --path PATH        Path to the project directory.
  -a, --alt_folder       Altenate folder structure(./arc/episode)
  -n, --name TEXT        Name of the project saved in config.
  -e, --episode INTEGER  Episode you want to mux.
  -r, --repeat           Repeat last muxing action.
  -o, --output           See whole output of Subkt.
  --help                 Show this message and exit.
```

At any point, you can run `muxkt config <command>` to add or remove projects from the config or manually edit the config in the editor. Following is the help page of `muxkt config --help`
```
Usage: muxkt config [OPTIONS] COMMAND [ARGS]...

  Add, remove, edit projects in the config.

Options:
  --help  Show this message and exit.

Commands:
  add     Add projects to config.
  edit    Manually edit the config.
  remove  Remove projects from the config.
```

# Alternate Folder Structure
This program has a flag `muxkt mux -a` for alternate folder structure. You will probably never have to use this but I have implemented this folder structure for a couple of my projects thus I have added this here. The folder structure looks like this:
```.
├── 01 Name of Arc 1/ Season 1
│   ├── 01
│   ├── 02
│   └── ...
├── 02 Name of Arc2/ Season 2
│   ├── 01
│   ├── 02
│   └── ...
├── ...
│   ├── ...
└── Subkt Configs
```
This folder structure became necessary for me because I was handling projects of hundreds of epidodes and thus I had to divide the episodes in their respective arcs. If you have this folder structure, use `-a` flag while muxing and the project will prompt you to choose both an arc and the episode of that arc for muxing.

To explain briefly, instead of doing `mux.01`, we're doing `mux.arc_01` where, for automation, I set `arc` in sub.properties by taking the folder name of the arc, remove first 3 characters, make everything lowercase and remove space. So, for example, if the folder name was `02 Orange Town`, removing first 3 characters gives `Orange Town`, then making lowercase gives `orange town` and removing spaces gives `orangetown`. Thus, to mux episode 1 of arc `Orange Town`, the SubKt commands becomes `mux.orangetown_01`.

If the `arc` in the sub.properties has not been set to follow this rule, then the exception can be defined in config under `Exceptions` section as follows where key is what would it be if it followed the rule above and value is what is actually set in sub.properties:

```
[Exceptions]
davybackfight = dbf
```
