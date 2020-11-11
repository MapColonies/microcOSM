# Osmosis

Osmosis is a command line Java application for processing OSM data. The tool consists of pluggable components that can be chained to perform a larger operation. For example, it has components for reading/writing databases and files, deriving/applying changes to data sources, and sorting data, (etc.). It has been written to easily add new features without re-writing common tasks such as file and database handling.

Some examples of the things it can currently do are:

* Generate planet dumps from a database
* Load planet dumps into a database
* Produce change sets using database history tables
* Apply change sets to a local database
* Compare two planet dump files and produce a change set
* Re-sort the data contained in planet dump files
* Extract data inside a bounding box or polygon

more info can be found [**here**](https://wiki.openstreetmap.org/wiki/Osmosis), [Github repo](https://github.com/openstreetmap/osmosis)
