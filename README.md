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

# Folder Structure

Muxkt supports two folder structures: normal and alternate.

## Normal Folder Structure

All the episode folders are available in the same folder as the subkt files. This folder structure is what most of the people will use.

```
.
├── 01
├── 02
├── 03
├── ...
└── Subkt Configs
```

## Alternate Folder Structure

All the episode folders are available in the sub folders. This is useful for long series divided by arcs or seasons.

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

Setting subkt to support this kind of folder structure is not covered in subkt docs. More info on it is at the bottom of this page.

# Usage

Muxkt has commands just like git where the command after `muxkt` informs the program what it should do. Currently, the commands present are mux and config. Additionally, there are help pages for all commands.

```
# To see the list of all availalble commands
muxkt -h

# To see the help for mux command
muxkt mux -h

# Similarly, to see the help for config commands
muxkt config -h
```

If you're running the script for the first time, I advise you to run `muxkt config add` to add as many projects as you have with their names, their path and their folder structure to the config. Project name with space is not valid.

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
# Interactive mode. Just run the following command and let the script handle it. It will allow you to choose what project and which episode you want to mux.
muxkt mux

# Provide project name and episode as positional argument. It muxes episode 4 of project named komi.
muxkt mux komi 4

# You can mux multiple episodes. The following muxes 4 5 and 12 of project named komi.
muxkt mux komi 4 5 12

# You can repeat last mux. It will repeat whatever project, episode you muxed last time.
muxkt mux -r

# You can pass custom flags if you use in the gradle command line.
muxkt mux -c -Pargs

# In case you want to view the unformatted output of last mux that subkt gave
muxkt mux -o
```

# Showcase

Here's an example preview of what the result looks like.

![showcase](https://github.com/user-attachments/assets/4e569f19-d172-4ed8-813a-a0588477bd91)

# Setting up alternate folder structure in subkt

If you have this folder structure, choose `alternate` folder structure when you add a project to config. Then when you try to mux this project, muxkt will prompt you to choose both an arc and the episode of that arc for muxing.

To explain briefly, instead of doing `mux.01`, we're doing `mux.arc_01`. Normally in `sub.properties`, you'd set episodes like this:

```
showkey=Naruto
episodes={01..24}|12.5
dialogue=$episode/$showkey $episode dialogue.ass
```

However, for alternate folder structure, I set episode as:

```
episodes=s1_{01..24}|s2_{01..24}

showkey=${episode.split('_')[0]}       # Gives prefix before _ (eg. s1, s2)
ep=${episode.split('_')[1]}            # Gives suffix after _ (eg. {01..24})

season1_*.folder=01 S1
season2_*.folder=02 S2

# Returns something like '01 S1/02/02 dialogue.ass'
dialogue=${folder}/${ep}/${ep} dialogue.ass
```

Let us say that you have a folder structure like this:

```.
├── 01 Romance Dawn
│   ├── 01
│   ├── 02
│   └── ...
├── 02 Orange Town
│   ├── 01
│   ├── 02
│   └── ...
├── build.gradle.kts
└── sub.properties
```

Here, folder and episodes are related because if we take a folder, remove first 3 characters and make it lowercase, we get the prefix for the episode.

So, for example, if the folder name was `02 Orange Town`, removing first 3 characters gives `Orange Town`, then making lowercase gives `orange town` and removing spaces gives `orangetown`. Thus, to mux episode 1 of arc `Orange Town`, the SubKt commands becomes `mux.orangetown_01`.

There can be exceptions to this rule. i.e instead of running `mux.orangetown_01`, what if you've set up subkt to use `mux.ot_01` command.

When you add the project to the config, you can also set up this exceptions.
Give what is expected `(orangetown)` in this case as key and `(ot)` as value of exception.
``
