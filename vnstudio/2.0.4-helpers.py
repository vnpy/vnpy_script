import os
import winreg
from typing import List


def is_same_file(path1: str, path2: str):
    try:
        return os.path.samefile(path1, path2)
    except FileNotFoundError:
        return False


type_mapper = {str: winreg.REG_SZ, int: winreg.REG_DWORD, bytes: winreg.REG_BINARY}
sys_reg_root = winreg.HKEY_LOCAL_MACHINE
sys_reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

user_reg_root = winreg.HKEY_CURRENT_USER
user_reg_path = r"Environment"


def get_key(root, path: str, key: str):
    try:
        with winreg.OpenKey(root, path) as k:
            val, reg_type = winreg.QueryValueEx(k, key)
            return val
    except WindowsError:
        return None


def set_key(root, path: str, key: str, val: any):
    with winreg.CreateKey(root, path) as k:
        reserved = 0
        winreg.SetValueEx(k, key, reserved, type_mapper[type(val)], val)


def get_sys_path() -> List[str]:
    path: str = get_key(sys_reg_root, sys_reg_path, "Path")
    return path.split(';') if path else []


def set_sys_path(new_value: List[str]):
    set_key(sys_reg_root, sys_reg_path, "Path", ";".join(new_value))


def get_user_path() -> List[str]:
    path: str = get_key(user_reg_root, user_reg_path, "Path")
    return path.split(';') if path else []


def set_user_path(new_value: List[str]):
    set_key(user_reg_root, user_reg_path, "Path", ";".join(new_value))


def add_to_user_path(new_path: str, ):
    """
    Add **one** path into PATH of current user
    """
    assert ';' not in new_path
    old_fixed_paths = get_user_path()
    for p in old_fixed_paths:
        if is_same_file(p, new_path):
            return
    old_paths = get_user_path()
    return set_user_path([new_path, *old_paths])


def add_to_sys_path(new_path: str):
    """
    Add **one** path into PATH of SYSTEM
    """
    assert ';' not in new_path
    old_fixed_paths = get_sys_path()
    for p in old_fixed_paths:
        if is_same_file(p, new_path):
            return
    old_paths = get_sys_path()
    return set_sys_path([new_path, *old_paths])


def remove_from_user_path(path: str):
    """
    Remove **one** path from PATH of current user
    """
    assert ';' not in path
    old_paths = get_user_path()
    new_paths = [i for i in old_paths if not is_same_file(i, path)]
    if new_paths != old_paths:
        return set_user_path(new_paths)


def remove_from_sys_path(path: str):
    """
    Remove **one** path from PATH of SYSTEM
    """
    assert ';' not in path
    old_paths = get_sys_path()
    new_paths = [i for i in old_paths if not is_same_file(i, path)]
    if new_paths != old_paths:
        return set_sys_path(new_paths)


def get_vnstudio_root():
    import vnstation
    path: str = vnstation.__path__[0]
    root = os.path.join(path, "..", "..", "..")
    return os.path.abspath(root)


# write new files
vnstudio_root = get_vnstudio_root()
helpers_dirs = os.path.join(vnstudio_root, "helpers")
if not os.path.exists(helpers_dirs):
    raise Exception("只支持VNStudio的升级。")

files = {
    'add_into_sys_path.py': 'from python_path import python_root, python_scripts_root\nfrom win_env_path import add_to_sys_path\n\n\ndef main():\n    add_to_sys_path(python_root)\n    add_to_sys_path(python_scripts_root)\n\n\nif __name__ == "__main__":\n    main()\n',
    'add_into_user_path.py': 'from python_path import python_root, python_scripts_root\nfrom win_env_path import add_to_user_path\n\n\ndef main():\n    add_to_user_path(python_root)\n    add_to_user_path(python_scripts_root)\n\n\nif __name__ == "__main__":\n    main()\n',
    'path_utils.py': 'import os\n\n\ndef is_same_file(path1: str, path2: str):\n    try:\n        return os.path.samefile(path1, path2)\n    except FileNotFoundError:\n        return False\n\n',
    'python_path.py': 'import os\n\n_mydir = os.path.dirname(__file__)  # <Python>/helpers\n\npython_root = os.path.abspath(os.path.join(_mydir, "../"))\npython_scripts_root = os.path.abspath(os.path.join(python_root, "Scripts"))\n',
    'remove_from_sys_path.py': 'from python_path import python_root, python_scripts_root\nfrom win_env_path import remove_from_sys_path\n\n\ndef main():\n    remove_from_sys_path(python_root)\n    remove_from_sys_path(python_scripts_root)\n\n\nif __name__ == "__main__":\n    main()\n',
    'remove_from_user_path.py': 'from python_path import python_root, python_scripts_root\nfrom win_env_path import remove_from_user_path\n\n\ndef main():\n    remove_from_user_path(python_root)\n    remove_from_user_path(python_scripts_root)\n\n\nif __name__ == "__main__":\n    main()\n',
    'win_env_path.py': 'import winreg\nfrom typing import List\n\nfrom path_utils import is_same_file\n\ntype_mapper = {str: winreg.REG_SZ, int: winreg.REG_DWORD, bytes: winreg.REG_BINARY}\nsys_reg_root = winreg.HKEY_LOCAL_MACHINE\nsys_reg_path = r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"\n\nuser_reg_root = winreg.HKEY_CURRENT_USER\nuser_reg_path = r"Environment"\n\n\ndef get_key(root, path: str, key: str):\n    try:\n        with winreg.OpenKey(root, path) as k:\n            val, reg_type = winreg.QueryValueEx(k, key)\n            return val\n    except WindowsError:\n        return None\n\n\ndef set_key(root, path: str, key: str, val: any):\n    with winreg.CreateKey(root, path) as k:\n        reserved = 0\n        winreg.SetValueEx(k, key, reserved, type_mapper[type(val)], val)\n\n\ndef get_sys_path() -> List[str]:\n    path: str = get_key(sys_reg_root, sys_reg_path, "Path")\n    return path.split(\';\') if path else []\n\n\ndef set_sys_path(new_value: List[str]):\n    set_key(sys_reg_root, sys_reg_path, "Path", ";".join(new_value))\n\n\ndef get_user_path() -> List[str]:\n    path: str = get_key(user_reg_root, user_reg_path, "Path")\n    return path.split(\';\') if path else []\n\n\ndef set_user_path(new_value: List[str]):\n    set_key(user_reg_root, user_reg_path, "Path", ";".join(new_value))\n\n\ndef add_to_user_path(new_path: str, ):\n    """\n    Add **one** path into PATH of current user\n    """\n    assert \';\' not in new_path\n    old_fixed_paths = get_user_path()\n    for p in old_fixed_paths:\n        if is_same_file(p, new_path):\n            return\n    old_paths = get_user_path()\n    return set_user_path([new_path, *old_paths])\n\n\ndef add_to_sys_path(new_path: str):\n    """\n    Add **one** path into PATH of SYSTEM\n    """\n    assert \';\' not in new_path\n    old_fixed_paths = get_sys_path()\n    for p in old_fixed_paths:\n        if is_same_file(p, new_path):\n            return\n    old_paths = get_sys_path()\n    return set_sys_path([new_path, *old_paths])\n\n\ndef remove_from_user_path(path: str):\n    """\n    Remove **one** path from PATH of current user\n    """\n    assert \';\' not in path\n    old_paths = get_user_path()\n    new_paths = [i for i in old_paths if not is_same_file(i, path)]\n    if new_paths != old_paths:\n        return set_user_path(new_paths)\n\n\ndef remove_from_sys_path(path: str):\n    """\n    Remove **one** path from PATH of SYSTEM\n    """\n    assert \';\' not in path\n    old_paths = get_sys_path()\n    new_paths = [i for i in old_paths if not is_same_file(i, path)]\n    if new_paths != old_paths:\n        return set_sys_path(new_paths)\n'
}

for filename, data in files.items():
    path = os.path.join(helpers_dirs, filename)
    with open(path, 'wt') as f:
        f.write(data)
print("更新成功！")

restores = [
    '%SystemRoot%\\system32',
    '%SystemRoot%',
    '%SystemRoot%\\System32\\Wbem',
    '%SYSTEMROOT%\\System32\\WindowsPowerShell\\v1.0\\',
    '%SYSTEMROOT%\\System32\\OpenSSH\\',
]

restore_failed = False
for path in restores:
    try:
        add_to_sys_path(path)
    except WindowsError:
        restore_failed = True
        pass

if restore_failed:
    print("恢复系统环境变量失败。若要恢复系统环境变量，请确保你使用管理员权限运行！")
