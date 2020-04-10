from asyncio import run, start_server
from asyncio.streams import StreamReader, StreamWriter
from argparse import ArgumentParser
from jdb.jql import JQL, TERMINATOR, EXIT
from jdb.db import DB
from pyparsing import ParseException


class Client:
    def __init__(self, writer: StreamWriter, reader: StreamReader, db: DB):
        self.jql = JQL()
        self.writer = writer
        self.reader = reader
        self.db = db

    async def async_loop(self):
        reader, writer = self.reader, self.writer

        while True:
            data = await reader.readuntil(TERMINATOR.encode())
            result = await self._async_call(data.decode())
            if result[0] == EXIT:
                break

        writer.close()

    async def _async_call(self, txt: str):
        writer = self.writer

        try:
            statement = self.jql.parse(txt)
            writer.write(b"OK\n")
            return statement
        except ParseException as err:
            writer.write(f"SYNTAX ERROR: line {err.lineno}, col {err.col}\n".encode())

        await writer.drain()


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.db = DB()

    async def async_start(self):
        host, port = self.host, self.port
        server = await start_server(self._async_client_connected, host, port)
        print(f"[{host}:{port}] listening")

        async with server:
            await server.serve_forever()

    async def _async_client_connected(self, reader: StreamReader, writer: StreamWriter):
        client = Client(reader=reader, writer=writer, db=self.db)
        await client.async_loop()


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
