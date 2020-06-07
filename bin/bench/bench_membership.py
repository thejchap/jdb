from typing import Dict
import json
from os import path, makedirs
from time import sleep
from threading import Thread
from structlog import get_logger
from jdb import server as srv, membership as mbr

_DIRNAME = path.dirname(__file__)
_LOGGER = get_logger()
_VERSION = "4 improved random target selection"


def _main(sample: int):
    """
    fire up a bunch of servers, kill one, see how long it takes for them to all find out
    """

    n = 20
    processes = []
    servers = []
    target_key = "node0000=127.0.0.1:2337"

    for i in range(0, n):
        port = 1337 + i
        p2p_port = 2337 + i
        name = f"node{i:04d}"
        join = None

        if i > 0:
            join = "node0000=127.0.0.1:2337"

        server = srv.Server(node_name=name, port=port, p2p_port=p2p_port, join=join)
        thread = Thread(target=server.start, name=name, daemon=True)
        processes.append(thread)
        servers.append(server)

    for process in processes:
        process.start()

    n = len(servers)

    while True:
        sizes = {len(list(s.node.membership.cluster_state)) for s in servers}

        if len(sizes) == 1 and n in sizes:
            break

        sleep(0.5)

    _LOGGER.info("all bootstrapped")
    sleep(mbr.STARTUP_GRACE_PERIOD * n)
    _LOGGER.info(f"killing {target_key}")
    target = servers.pop(0)
    target.stop()
    _LOGGER.info(f"killed {target_key}")

    results: Dict = {}
    poll_interval = 0.05
    j = 0

    while True:
        states = {
            s.node_name: set(
                map(lambda k: k.decode(), dict(s.node.membership.cluster_state).keys())
            )
            for s in servers
        }

        i = 0

        for nstate in states.values():
            if target_key in nstate:
                i += 1

        results[j * poll_interval] = i
        _LOGGER.info("bench.state_poll", states=states)
        j += 1

        if i == 0:
            break

        sleep(poll_interval)

    dname = "|".join(
        map(
            str,
            [
                f"fdi:{mbr.FD_INTERVAL}",
                f"fds:{mbr.FD_SUBGROUP_SIZE}",
                f"gi:{mbr.GOSSIP_INTERVAL}",
                f"gs:{mbr.GOSSIP_SUBGROUP_SIZE}",
            ],
        )
    )

    datapath = path.join(_DIRNAME, "data", "membership", str(_VERSION), dname)

    if not path.exists(datapath):
        makedirs(datapath)

    with open(path.join(datapath, f"{sample}.json"), "w") as file:
        file.write(json.dumps(results))

    for server in servers:
        server.node.membership.stop()

    for server in servers:
        server.stop()

    for process in processes:
        process.join()


if __name__ == "__main__":
    samp_start = 2
    samp_finish = 3

    for samp in range(samp_start, samp_finish):
        _main(samp)
