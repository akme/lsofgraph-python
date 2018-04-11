#!/usr/bin/env python
# Convert the output of `lsof -F` into PID USER CMD OBJ
import sys


def parse_lsof():
    procs = {}
    cur = {}
    proc = {}
    file = {}

    for line in sys.stdin:

        if line.startswith("COMMAND"):
            print 'did you run lsof without -F?'
            exit(1)

        tag = line[0]
        val = line[1:].rstrip('\n')
        if tag == 'p':
            if val not in procs:
                proc = {'files': []}
                file = None
                cur = proc
                procs[val] = proc
            else:
                proc = {}
                cur = {}
        elif tag == 'f' and proc:
            file = {'proc': proc}
            cur = file
            proc['files'].append(file)

        if cur:
            cur[tag] = val

        # skip kernel threads

        if proc:
            if file and all(k in file.keys() for k in ("f", "t")):
                if file['f'] == "txt" and file['t'] == "unknown":
                    procs[proc['p']] = {}
                    proc = {}
                    file = None
                    cur = None
    return procs


def find_connections(procs):
    cs = {
        'fifo': {},
        'unix': {},
        'tcp': {},
        'udp': {},
        'pipe': {}
    }
    for pid, proc in procs.iteritems():
        if 'files' in proc:
            for _, file in enumerate(proc['files']):

                if 't' in file and file['t'] == "unix":
                    if 'i' in file:
                        i = file['i']
                        if i in cs['unix']:
                            cs['unix'][i].append(file)
                        else:
                            cs['unix'][i] = []
                            cs['unix'][i].append(file)
                    else:
                        i = file['d']
                        if i in cs['unix']:
                            cs['unix'][i].append(file)
                        else:
                            cs['unix'][i] = []
                            cs['unix'][i].append(file)

                if 't' in file and file['t'] == "FIFO":

                    if 'i' in file:
                        if file['i'] in cs['fifo']:
                            cs['fifo'][file['i']].append(file)
                        else:
                            cs['fifo'][file['i']] = []
                            cs['fifo'][file['i']].append(file)

                if 't' in file and file['t'] == "PIPE":
                    for n in file['n'].lstrip('->'):
                        ps = {file['d'], n}
                        ps = sorted(ps)
                        if len(ps) == 2:
                            id = ps[0] + "\\n" + ps[1]
                            fs = cs['pipe']
                            if id in fs:
                                fs[id].append(file)
                            else:
                                fs[id] = []
                                fs[id].append(file)

                if 't' in file and (file['t'] == 'IPv4' or file['t'] == 'IPv6'):
                    if '->' in file['n']:
                        a, b = file['n'].split("->")
                        ps = {a, b}
                        ps = sorted(ps)
                        if len(ps) == 2:
                            id = ps[0] + "\\n" + ps[1]
                            if file['P'] == "TCP":
                                fs = cs['tcp']
                                if id in fs:
                                    fs[id].append(file)
                                else:
                                    fs[id] = []
                                    fs[id].append(file)
                            else:
                                fs = cs['udp']
                                if id in fs:
                                    fs[id].append(file)
                                else:
                                    fs[id] = []
                                    fs[id].append(file)
    return cs


def print_graph(procs, conns):
    colors = {
        'fifo': "green",
        'unix': "purple",
        'tcp': "red",
        'udp': "orange",
        'pipe': "blue"
    }

    # Generate graph

    print("digraph G {")
    print(
        "\tgraph [ center=true, margin=0.2, nodesep=0.1, ranksep=0.3, rankdir=LR];")
    print(
        "\tnode [ shape=box, style=\"rounded,filled\" width=0, height=0, fontname=Helvetica, fontsize=10];")
    print("\tedge [ fontname=Helvetica, fontsize=10];")

    # Parent/child relationships

    for pid, proc in procs.iteritems():
        if 'R' in proc and proc['R'] == "1":
            color = "grey70"
        else:
            color = "white"
        if 'p' in proc and 'n' in proc:
            print("\tp%s [ label = \"%s\\n%s %s\" fillcolor=%s ];" %
                  (proc['p'], proc['n'], proc['p'], proc['L'], color))
        elif 'p' in proc:
            if 'L' in proc: # there could be no L flag if process running, but user was removed. lsof: no pwd entry for UID
                print("\tp%s [ label = \"%s\\n%s %s\" fillcolor=%s ];" %
                  (proc['p'], proc['c'], proc['p'], proc['L'], color))
            else:
                print("\tp%s [ label = \"%s\\n%s %s\" fillcolor=%s ];" %
                  (proc['p'], proc['c'], proc['p'], "no user", color))
        if 'R' in proc and proc['R'] in procs:
            proc_parent = procs[proc['R']]
            if proc_parent:
                if proc_parent['p'] != "1":
                    print(
                        "\tp%s -> p%s [ penwidth=2 weight=100 color=grey60 dir=\"none\" ];" % (proc['R'], proc['p']))

    for type, conn in conns.iteritems():
        for id, files in conn.items():
            if len(files) == 2:
                if files[0]['proc'] != files[1]['proc']:
                    label = type + ":\\n" + id
                    dir = "both"
                    if files[0]['a'] == "w":
                        dir = "forward"
                    elif files[0]['a'] == "r":
                        dir = "backward"
                    print("\tp%s -> p%s [ color=\"%s\" label=\"%s\" dir=\"%s\"];" % (
                        files[0]['proc']['p'], files[1]['proc']['p'], colors[type] or "black", label, dir))
    print("}")


if __name__ == '__main__':
    procs = parse_lsof()
    conns = find_connections(procs)
    print_graph(procs, conns)
