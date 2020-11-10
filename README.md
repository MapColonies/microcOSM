# microcOSM

microcosm aims to provide an easily installable package for the OpenStreetMap software stack.

## Docs
Click [here](https://mapcolonies.github.io/microcOSM/#/) to visit our documentation.

## Why?

OpenStreetMap runs open source software to manage geospatial data for the entire planet. It has given birth to an entire ecosystem of tools to edit, export and process spatial data.

Very often, one wants to manage geospatial datasets that cannot be added to the main OpenStreetMap project, either due to license restrictions, or because the data doesn't fit within the ambit of the OpenStreetMap project. However, it is still convenient and desirable to use the OpenStreetMap software backend, along with tools like JOSM to edit data, and `osmium` to export and process data.

The OpenStreetMap software stack has proven itself on a planetary scale, and has thousands of man hours of work behind it. This project aims to leverage this power, by making it simple to install and manage your own instance of the OpenStreetMap software.

## How?

This project provides docker container definitions for various aspects of the OpenStreetMap software stack, along with configuration scripts to run on a Kubernetes cluster.
