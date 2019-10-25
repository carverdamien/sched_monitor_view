# SchedDisplay

SchedDisplay is a visualization tool for [SchedLog](https://github.com/carverdamien/SchedLog), a custom ring buffer collecting scheduling events in the Linux kernel.

[![example](https://github.com/carverdamien/SchedDisplay/raw/master/docs/example.png)](https://github.com/carverdamien/SchedDisplay/raw/master/docs/example.png)

## Steps

1) Build and launch the webserver with `./docker` script.
2) Open the web app http://localhost:5006/v0.
3) Select a tarball file which contains the data recorded during an experiment and then click select. (see [below](#tarball) for record/import)
4) Select a json file which contains the instructions on how to build the lines in the image from the recorded data and then click select. Uploading a local json file is also supported. (see [below](#json) for writing custom instructions)
5) Select Figure to view the image.

There are additional tabs in the application.
The Console tab reports progress and errors.
The Stat tab computes statistics. 
The Var tab shows available events in the SchedLog kernel.

## Tarball

A tarball must at least contain the following files: ...

Check [RecordSchedLog](https://github.com/carverdamien/RecordSchedLog) to discover how we automate our experiments.

## Json

The `input` field lists the data required to build the image.
Some data are directly recorded through SchedLog (timestamp, cpu, event, pid, arg0, arg1).
Other data must be computed.

The `output` field lists the data to store in the image.
Some data are mandatory (x0,y0,x1,y1,c).

Tbe `c` field lists instructions on how to build categories of lines.
