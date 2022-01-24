import asyncio
import os
import logging
from aiohttp import web
import aiofiles

STREAM_DELAY = int(os.getenv("STREAM_DELAY", 0))
DEBUG_PRINT = os.getenv("DEBUG_PRINT", "False").lower() in ("true", "1", "yes")
CONTENT_PATH = os.getenv("CONTENT_PATH", "test_photos")

if DEBUG_PRINT:
    logging_level = logging.DEBUG
else:
    logging_level = logging.CRITICAL

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging_level)


async def archivate(request):
    response = web.StreamResponse()

    name = request.match_info.get("archive_hash", "Anonymous")

    path_to_folder = os.path.abspath(f"{CONTENT_PATH}/{name}/")
    if not os.path.exists(path_to_folder):
        raise web.HTTPNotFound(text="Архив не существует или был удален",
                               content_type="text/html")

    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = f'attachment; ' \
                                              f'filename = "{name}.zip"'

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    proc = await asyncio.create_subprocess_exec(
        "zip", "-",  "-rj", "-q", f"{path_to_folder}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        while not proc.stdout.at_eof():
            chunk = await proc.stdout.read(100 * 1024)
            logging.debug("Sending archive chunk ...")
            await response.write(chunk)
            await asyncio.sleep(STREAM_DELAY)
    except asyncio.CancelledError:
        logging.debug("Download was interrupted  ...")
    finally:
        if proc.returncode is None:
            proc.kill()
            logging.debug("Process zip was killed ...")
        await proc.communicate()


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
