import shutil
import subprocess
from pathlib import Path


DOIT_CONFIG = {
    "default_tasks": ["html"],
}


SERVER_PY = Path("mood/server/server.py")

PO_DIR = Path("mood/server/po")
RU_DIR = PO_DIR / "ru" / "LC_MESSAGES"

POT_FILE = PO_DIR / "server.pot"
PO_FILE = RU_DIR / "server.po"
MO_FILE = RU_DIR / "server.mo"

DOC_DIR = Path("docs")
BUILD_DIR = Path("build")
DOC_CONF = DOC_DIR / "conf.py"
DOC_INDEX = DOC_DIR / "index.rst"
HTML_INDEX = BUILD_DIR / "html" / "index.html"


def clean_targets(targets):
    def clean():
        for target in targets:
            target = Path(target)
            if target.exists():
                target.unlink()
    return clean


def clean_html():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)


def extract_messages():
    PO_DIR.mkdir(parents=True, exist_ok=True)

    strings = []
    text = SERVER_PY.read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()
        if "_(" in line:
            start = line.find('_("')
            if start != -1:
                start += 3
                end = line.find('")', start)
                if end != -1:
                    strings.append(line[start:end])

    with POT_FILE.open("w", encoding="utf-8") as f:
        f.write('msgid ""\n')
        f.write('msgstr ""\n')
        f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        f.write('"Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : '
                'n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);\\n"\n\n')

        for s in strings:
            f.write(f'msgid "{s}"\n')
            f.write('msgstr ""\n\n')

        f.write('msgid "{} hp"\n')
        f.write('msgid_plural "{} hp"\n')
        f.write('msgstr[0] "{} очко здоровья"\n')
        f.write('msgstr[1] "{} очка здоровья"\n')
        f.write('msgstr[2] "{} очков здоровья"\n\n')


def update_po():
    RU_DIR.mkdir(parents=True, exist_ok=True)

    translations = {
        "Set up locale: {}": "Установлена локаль: {}",
        "{} entered the MUD": "{} вошёл в MUD",
        "{} left the MUD": "{} вышел из MUD",
        "{} added monster {} to ({}, {}) saying {} with {}":
            "{} добавил монстра {} в ({}, {}), говорящего {}, с {}",
        "{} attacked {} with {}, damage {}, {} died":
            "{} атаковал {} с помощью {}, урон {}, {} умер",
        "{} attacked {} with {}, damage {}, {} now has {}":
            "{} атаковал {} с помощью {}, урон {}, у {} теперь {}",
    }

    with PO_FILE.open("w", encoding="utf-8") as f:
        f.write('msgid ""\n')
        f.write('msgstr ""\n')
        f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        f.write('"Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : '
                'n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);\\n"\n\n')

        for msgid, msgstr in translations.items():
            f.write(f'msgid "{msgid}"\n')
            f.write(f'msgstr "{msgstr}"\n\n')

        f.write('msgid "{} hp"\n')
        f.write('msgid_plural "{} hp"\n')
        f.write('msgstr[0] "{} очко здоровья"\n')
        f.write('msgstr[1] "{} очка здоровья"\n')
        f.write('msgstr[2] "{} очков здоровья"\n')


def compile_mo():
    RU_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["msgfmt", str(PO_FILE), "-o", str(MO_FILE)],
        check=True,
    )


def make_docs_sources():
    DOC_DIR.mkdir(exist_ok=True)

    DOC_CONF.write_text(
        """
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "MUD"
extensions = ["sphinx.ext.autodoc"]
html_theme = "alabaster"
""".strip() + "\n",
        encoding="utf-8",
    )

    DOC_INDEX.write_text(
        """
MUD documentation
=================

.. automodule:: mood.server.server
   :members:

.. automodule:: mood.common.game
   :members:

.. automodule:: mood.client.client
   :members:
""".strip() + "\n",
        encoding="utf-8",
    )


def task_i18n_extract():
    return {
        "actions": [extract_messages],
        "file_dep": [SERVER_PY],
        "targets": [POT_FILE],
        "clean": [clean_targets([POT_FILE])],
    }


def task_i18n_update():
    return {
        "actions": [update_po],
        "file_dep": [POT_FILE],
        "targets": [PO_FILE],
        "task_dep": ["i18n_extract"],
        "clean": [clean_targets([PO_FILE])],
    }


def task_i18n_compile():
    return {
        "actions": [compile_mo],
        "file_dep": [PO_FILE],
        "targets": [MO_FILE],
        "task_dep": ["i18n_update"],
        "clean": [clean_targets([MO_FILE])],
    }


def task_i18n():
    return {
        "actions": None,
        "task_dep": ["i18n_extract", "i18n_update", "i18n_compile"],
    }


def task_docs_sources():
    return {
        "actions": [make_docs_sources],
        "targets": [DOC_CONF, DOC_INDEX],
        "clean": [clean_targets([DOC_CONF, DOC_INDEX])],
    }


def task_html():
    return {
        "actions": [["sphinx-build", "-M", "html", str(DOC_DIR), str(BUILD_DIR)]],
        "file_dep": list(Path("mood").rglob("*.py")),
        "targets": [HTML_INDEX],
        "task_dep": ["docs_sources"],
        "clean": [clean_html],
    }


def task_test():
    return {
        "actions": [["python", "-m", "unittest", "./mood/tests/test_server_client.py"]],
        "task_dep": ["i18n"],
        "clean": [],
    }


def task_erase():
    return {
        "actions": [
            clean_html,
            clean_targets([POT_FILE, PO_FILE, MO_FILE, DOC_CONF, DOC_INDEX]),
        ],
    }
