from asyncio import open_connection, run
from asyncio.streams import StreamReader, StreamWriter
from argparse import ArgumentParser
from jdb.jql import TERMINATOR, EXIT


def _prompt(prompt: str):
    while True:
        statement = ""

        while True:
            txt = input(prompt)
            if TERMINATOR in txt:
                statement += f"{txt.split(TERMINATOR)[0]};"
                break
            statement += f"{txt}\n"
        yield statement


async def _async_main():
    parser = ArgumentParser(description="jdb client")
    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    args = parser.parse_args()
    prompt = f"{args.host}:{args.port}> "
    reader: StreamReader
    writer: StreamWriter
    reader, writer = await open_connection(args.host, args.port)

    try:
        for statement in _prompt(prompt):
            try:
                writer.write(statement.encode())
                await writer.drain()
                res = await reader.readline()
                print(res.decode().rstrip())
            except ConnectionResetError as err:
                print(err)
    except KeyboardInterrupt:
        pass

    writer.write(f"{EXIT};".encode())
    await writer.drain()
    writer.close()


if __name__ == "__main__":
    run(_async_main())
