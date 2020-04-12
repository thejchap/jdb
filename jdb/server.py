from typing import Dict, Any
from asyncio import run, start_server
from asyncio.streams import StreamReader, StreamWriter
from argparse import ArgumentParser
from pyparsing import ParseException
from structlog import get_logger
from jdb.jql import JQL, TERMINATOR, SYNTAX_ERR
from jdb.db import DB
from jdb.id import ID, id_to_str, gen_id

_LOGGER = get_logger()


class Client:
    clientid: ID
    reader: StreamReader
    writer: StreamWriter
    jql: JQL

    def __init__(self, writer: StreamWriter, reader: StreamReader, db: DB, logger: Any):
        self.jql = JQL(db=db)
        self.writer = writer
        self.reader = reader
        self.clientid = gen_id()
        self._logger = logger.bind(
            clientid=id_to_str(self.clientid), clientpeername=self.peername
        )

    @property
    def peername(self):
        return self.writer.get_extra_info("peername")

    async def async_loop(self):
        reader, writer = self.reader, self.writer

        while True:
            data = await reader.readuntil(TERMINATOR.encode())
            raw = data.decode()[:-1]

            if not len(raw):
                break

            await self._async_call(raw)

        writer.close()

    async def _async_call(self, statement: str):
        writer = self.writer
        self._logger.debug("statement", statement=statement)

        try:
            result, txn = self.jql.call(statement=statement)
            self._logger.debug(
                "result", result=result, txnid=(txn.txnid if txn else None)
            )
            writer.write(f"{result}\n".encode())
        except ParseException as err:
            self._logger.err(err)
            writer.write(f"{SYNTAX_ERR}: ln {err.lineno}, col {err.col}\n".encode())
        finally:
            await writer.drain()

        return None


class Server:
    nodeid: ID
    db: DB
    host: str
    port: int
    clients: Dict[ID, Client]

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.db = DB()
        self.nodeid = gen_id()
        self.clients: Dict[str, Client] = {}

    async def async_start(self):
        host, port = self.host, self.port
        server = await start_server(self._async_client_connected, host, port)

        self._logger.msg("listening")

        async with server:
            await server.serve_forever()

    async def _async_client_connected(self, reader: StreamReader, writer: StreamWriter):
        client = Client(reader=reader, writer=writer, db=self.db, logger=self._logger)

        self._logger.msg(
            "client connected",
            clientid=id_to_str(client.clientid),
            clientpeername=client.peername,
        )

        if client.peername in self.clients:
            raise Exception("client collision")

        self.clients[client.clientid] = client

        try:
            await client.async_loop()
        except ConnectionResetError:
            pass
        finally:
            self._logger.msg(
                "client disconnected",
                clientid=id_to_str(client.clientid),
                clientpeername=client.peername,
            )

            del self.clients[client.clientid]

    @property
    def _logger(self):
        return _LOGGER.bind(
            nodeid=id_to_str(self.nodeid), host=self.host, port=self.port
        )


def _main():
    parser = ArgumentParser(description="jdb server")
    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    args = parser.parse_args()
    server = Server(host=args.host, port=args.port)

    try:
        run(server.async_start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    _main()
