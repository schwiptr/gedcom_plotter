# gedcom_plotter

Plot a family tree stored in a gedcom file using graphviz.  
See an example [here](example/Bible+Family+Tree.svg?raw=true) (based on the gedcom file [Bible+Family+Tree.ged](https://sourceforge.net/projects/godskingsheroes/files/ged%20files/religious%20figures%20and%20systems/)).

## Installation

Tested in Ubuntu 22:

    apt update
    apt install gcc python3-dev python3-venv graphviz libgraphviz-dev

    python3 -m venv env
    source env/bin/activate

    pip3 install git+https://github.com/schwiptr/gedcom_plotter.git

## Usage
See `gedcom_plotter --help` for details.  
The example above was created using this command:  
`gedcom_plotter Bible+Family+Tree.ged -o Bible+Family+Tree.svg -e gray`
