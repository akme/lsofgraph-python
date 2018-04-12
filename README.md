Python version of [zevv/lsofgraph](https://github.com/zevv/lsofgraph)

A small utility to convert Unix `lsof` output to a graph showing FIFO and UNIX interprocess communication.

Generate graph:

````shell
sudo lsof -n -F | python lsofgraph.py | dot -Tjpg > /tmp/a.jpg
    OR
sudo lsof -n -F | python lsofgraph.py | dot -T svg > /tmp/a.svg
````

or add `unflatten` to the chain for a better layout:

````shell
sudo lsof -n -F | python lsofgraph.py | unflatten -l 1 -c 6 | dot -T jpg > /tmp/a.jpg
    OR
sudo lsof -n -F | python lsofgraph.py | unflatten -l 1 -c 6 | dot -T svg > /tmp/a.svg
````

![example output](/example.jpg)
