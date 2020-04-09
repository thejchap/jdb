from asyncio import run, start_server
from asyncio.streams import StreamReader, StreamWriter
from argparse import ArgumentParser
from jdb.jql import JQL, TERMINATOR, EXIT
from pyparsing import ParseException


async def async_handler(reader: StreamReader, writer: StreamWriter):
    host, port = writer.get_extra_info("peername")
    print(f"[{host}:{port}] connected")
    jql = JQL()

    while True:
        data = await reader.readuntil(TERMINATOR.encode())

        try:
            statement = jql.parse(data.decode())
            print(f"[{host}:{port}] statement: {statement!r}")
            writer.write(b"OK\n")

            if statement[0] == EXIT:
                break
        except ParseException as err:
            print(f"[{host}:{port}] {err}")
            writer.write(f"SYNTAX ERROR: line {err.lineno}, col {err.col}\n".encode())

        await writer.drain()

    print(f"[{host}:{port}] disconnected")
    writer.close()


async def _async_start_server(host: str, port: int):
    server = await start_server(async_handler, host, port)
    print(f"[{host}:{port}] listening")

    async with server:
        await server.serve_forever()


def _main():
    parser = ArgumentParser(description="jdb server")
    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    args = parser.parse_args()

    try:
        run(_async_start_server(host=args.host, port=args.port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    _main()
