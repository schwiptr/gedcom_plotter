# gedcom_plotter

Plot a family tree stored in a gedcom file using graphviz.
See examples [here](examples/Bible+Family+Tree.svg?raw=true) and [here](examples/George+Washington+Family+Big.svg?raw=true) (based on gedcom files from [here](https://sourceforge.net/projects/godskingsheroes)).

## Installation

### Linux:

It is recommended to use a [venv](https://docs.python.org/3/library/venv.html) for installation.

Dependencies:
- python & pip
- graphviz (including devel packages)
- (git)

#### Ubuntu 22:

    apt update
    apt install gcc python3-dev python3-venv graphviz libgraphviz-dev

    python3 -m venv env
    source env/bin/activate

    pip3 install git+https://github.com/schwiptr/gedcom_plotter.git

#### Rocky Linux 9:

    dnf install 'dnf-command(config-manager)'
    dnf config-manager --enable crb
    dnf install git gcc python3-devel graphviz-devel

    python3 -m venv env
    source env/bin/activate

    pip3 install git+https://github.com/schwiptr/gedcom_plotter.git

### Windows:

Installation in Windows has currently only been tested using the Windows Subsystem for Linux (WSL), followed by the installation instructions for Linux above.

While it has not been tested, it should also be possible to install natively on Windows.
To do that, at least the following dependencies have to be installed:
- python
- Visual C/C++
- Graphviz
- (git)

See also [here](https://pygraphviz.github.io/documentation/stable/install.html#windows) the instructions for pygraphviz installation.

Using anaconda/miniconda for the installation in Windows is currently not recommended, as it results in font issues in the output plot.

## Usage
See `gedcom_plotter --help` for details.
The examples above were created using these commands:
    gedcom_plotter Bible+Family+Tree.ged -o Bible+Family+Tree.svg -e gray -g rankdir=BT
    gedcom_plotter.py George+Washington+Family+Big.ged -o George+Washington+Family+Big.svg -g rankdir=LR label="Family Tree of George Washington" labelloc=t fontsize=120 fontname="Z003" -n shape=oval style=filled fontname="Z003" width=2.4 -f M=#9abaed F=lightpink
