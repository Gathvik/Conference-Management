import os
import textwrap
from contextlib import suppress
from itertools import repeat
from pathlib import Path
from sys import executable
from virtual_conference import settings
from django.utils import timezone


def log_initial(*, debug, config_files, db_name, db_backend, LOG_DIR, plugins):
    from virtual_conference import __version__
    from utils.console import end_box, print_line, start_box

    with suppress(Exception):  # geteuid is not available on all OS
        if os.geteuid() == 0:
            print_line("You are running pretalx as root, why?", bold=True)

    lines = [
        (f"Virtual_Conference v{__version__}", True),
        (f'Settings:  {", ".join(config_files)}', False),
        (f"Database:  {db_name} ({db_backend})", False),
        # (f"Logging:   {LOG_DIR}", False),
        (f"Root dir:  {settings.BASE_DIR}", False),
        (f"Python:    {executable}", False),
        (f"Time: {timezone.datetime.now().ctime()}", False),
    ]
    # if plugins:
    #     plugin_lines = textwrap.wrap(", ".join(plugins), width=92)
    #     lines.append((f"Plugins:   {plugin_lines[0]}", False))
    #     lines += [(" " * 11 + line, False) for line in plugin_lines[1:]]
    if debug:
        lines += [("DEVELOPMENT MODE, DO NOT USE IN PRODUCTION!", True)]
    else:
        lines += [("PRODUCTION MODE", True)]
    image = """
____   _____________  
\   \ /   /\_   ___ \ 
 \   Y   / /    \  \/ 
  \     /  \     \____
   \___/    \______  /
                   \/ 

    """.strip().split(
        "\n"
    )
    img_width = len(image[0])
    image[-1] += " " * (img_width - len(image[-1]))
    image += [" " * img_width for _ in repeat(None, (len(lines) - len(image)))]

    lines = [(f"{image[n]}  {line[0]}", line[1]) for n, line in enumerate(lines)]

    size = max(len(line[0]) for line in lines) + 4
    start_box(size)
    for line in lines:
        print_line(line[0], box=True, bold=line[1], size=size)
    end_box(size)


def reduce_dict(data):
    return {
        section_name: {
            key: value for key, value in section_content.items() if value is not None
        }
        for section_name, section_content in data.items()
    }
