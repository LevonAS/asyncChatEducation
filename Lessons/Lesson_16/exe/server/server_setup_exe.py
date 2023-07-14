import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["common", "log", "server"],
    "includes": ['sqlalchemy', 'sqlite3', '_sqlite3'],
    "include_msvcr": True
}
setup(
    name="server_chat_Auuu",
    version="0.1.0",
    description="server_chat_Auuu",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('server_run.py',
                            base='Win32GUI',
                            target_name='server_chatAuuu.exe',
                            )]
)
