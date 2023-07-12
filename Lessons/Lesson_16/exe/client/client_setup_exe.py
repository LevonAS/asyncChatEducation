import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["common", "log", "client"],
    "includes": ['sqlalchemy', 'sqlite3', '_sqlite3'],
    "include_msvcr": True
}
setup(
    name="client_chat_Auuu",
    version="0.1.0",
    description="client_chat_Auuu",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('client_run.py',
                            base='Win32GUI',
                            target_name='client_chatAuuu.exe',
                            )]
)
