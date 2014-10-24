This directory is used to store temp files.

The only needed files here are:
  * RPT_ASNsGlobal
  * RPT_LinksGlobal

They contain a set of pre-processed data from the Global Routing table.
If the scripts can't find these files, the will be locally generated from
the file referenced in the `CONFIG['tabla_mundial']` variable in main.py.
DO NOT delete this files unless you have a very fast computer with
lots of RAM memory (12gb+).
