# Introduction

Muxkt is a wrapper for [SubKt](https://github.com/Myaamori/SubKt) that was written with the aim of sorting out the output of SubKt. While the output of SubKt is not bad, the important information can sometimes be hidden among a wall of text that is not entirely necessary to the end user to see. So this tool takes both the stdout and stderr of SubKt and presents in more digestable format. This began as a [bash script](https://github.com/PhosCity/muxsh) but I rewrote this in python for people who are in the environment where bash and GNU coreutils are not present in their system. I also wrote this to learn python and as such, the code may not be pleasant to look at.

## Main feature of muxkt

- It's config based where you can save any number of your current projects. You can thus run this script and choose from one of your projects to mux it's episodes.
- Choose a single or multiple episodes to mux then all at once.
- Sort both the stdout and stderr of SubKt and present them less verbosely.
- Make fatal errors more easier to see. (For example: The missing fonts are highlighted among the list of warnings.)
- Redo the last mux (single or mutiple episodes) with a flag.
- If you want to watch the original output of Subkt for the last mux you did, you can easily do so with a flag.
- Easily add or remove projects from the config. There is also a command to open the config in your default editor so that you can manually edit the config if you wish.
- Add custom gradle cli flags (example: -Pargs) to the command that is run.
- Support for alternate folder structure. Read more about alternate folder structure below.

# Installation

First ensure [Poetry is installed](https://python-poetry.org/docs/#installation).

Then run the following command:

    ```sh
    git clone https://github.com/PhosCity/muxkt.git \
    && cd muxkt \
    && poetry build \
    && pip install muxkt \
    && cd ..
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

It has commands just like git where the command after `muxkt` informs the program what it should do. Currently, the commands present are mux and config. Since you are most likely use mux comand a lot, I recommend you to alias `muxkt mux` to something like `mux` if you wish. Additionally, there are help pages for all commands.

```
# To see the list of all availalble commands
muxkt -h

# To see the help for mux command
muxkt mux -h

# Similarly, to see the help for config commands
muxkt config -h
```

If you're running the script for the first time, I advise you to run `muxkt config add` to add as many projects as you have and their corresponding path to the config. Project with space is not valid.

The following output of `muxkt mux --help` should give you a pretty decent idea of what is available to you while muxing. However, you can always just run `muxkt mux` and the program will guide you to do everything interactively as well.

```
Usage: muxkt mux [OPTIONS] [PROJECT] [EPISODE]...

  Mux the episodes using the arguments and the options provided by the user.

Options:
  -h, --help              Show this message and exit.
  -r, --repeat            Repeat last muxing action.
  -o, --output            See original output of previous mux
  -c, --custom_flag TEXT  Provide multiple custom Gradle flags (e.g., -Pkey=value).
```

Now let's say you added a project name called `komi` You have following options in the script:

```
# Interactive mode. Just run the following command and let the script handle it.
muxkt mux

# Provide project name and episode as positional argument. It muxes episode 4 of project named komi.
muxkt mux komi 4

# You can mux multiple episodes. The following muxes 4 5 and 12 of project named komi.
muxkt mux komi 4 5 12
```

# Alternate Folder Structure

This program supports an alternate folder structure. You will probably never have to use this but I have implemented this folder structure for a couple of the projects I'm in, so I have added this here. The folder structure looks like this:

```.
├── 01 Name of Arc 1/ Season 1
│   ├── 01
│   ├── 02
│   └── ...
├── 02 Name of Arc2/ Season 2
│   ├── 01
│   ├── 02
│   └── ...
├── ...
│   ├── ...
└── Subkt Configs
```

This folder structure became necessary for me because I was handling projects of hundreds of episodes and thus I had to divide the episodes in their respective arcs. If you have this folder structure, choose `alternate` folder structure when you add a project to config. Then when you try to mux this project, muxkt will prompt you to choose both an arc and the episode of that arc for muxing.

To explain briefly, instead of doing `mux.01`, we're doing `mux.arc_01` where, for automation, I set `arc` in sub.properties by taking the folder name of the arc, remove first 3 characters, make everything lowercase and remove space. So, for example, if the folder name was `02 Orange Town`, removing first 3 characters gives `Orange Town`, then making lowercase gives `orange town` and removing spaces gives `orangetown`. Thus, to mux episode 1 of arc `Orange Town`, the SubKt commands becomes `mux.orangetown_01`.

If the `arc` in the sub.properties has not been set to follow this rule, then the exception can be defined in config when you add the project to the config.
For example, the rule gives us `orangetown` as shown above but if you assigned this folder to `ot` in sub.properties, we need the command to be `mux.ot_01`.
So set exception for `orangetown` as `ot` when you are prompted to add exceptions.
``

# Showcase

Here's an example preview of what the result looks like.

![showcase](https://github.com/user-attachments/assets/4e569f19-d172-4ed8-813a-a0588477bd91)
