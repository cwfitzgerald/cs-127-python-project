import sys
import subprocess

python_modules_needed = ['anytree', 'flask']
packages_needed = ['libsqlite3-dev', 'libicu-dev', 'make', 'g++']


def status(name, success):
    return print("\t{} -- {}".format(name,
                                     "\u001b[32;1mSuccess\u001b[0m" if success else "\u001b[31;1mFailure\u001b[0m"))


def error(text):
    print("\u001b[31;1mERROR:\u001b[0m {}".format(text))
    exit(1)


def check_python_version():
    print("Checking python version:")

    success = sys.version_info.major == 3 and sys.version_info.minor >= 5
    name = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    status(name, success)

    if (not success):
        error("Please install python3.5 or greater")


def check_python_modules():
    print("Checking python modules:")

    successes = {}
    for module in python_modules_needed:
        successes[module] = subprocess.run([sys.executable, '-c', 'import {}'.format(module)],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please install {}".format(" ".join([name for name, result in successes.items() if not result])))


def check_system_packages():
    print("Checking system packages:")
    dpkg_query = subprocess.run(['dpkg-query', '--list'], stdout=subprocess.PIPE)

    names = [row.split()[1].partition(':')[0]
             for row in dpkg_query.stdout.decode('utf8').split('\n')[5:] if len(row) >= 2]

    successes = {package: package in names for package in packages_needed}

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please install {}".format(" ".join([name for name, result in successes.items() if not result])))


def check_submodules():
    print("Checking submodules:")
    submodule_status = subprocess.run(['git', 'submodule', 'status', '--recursive'], stdout=subprocess.PIPE)

    successes = {row.split()[1]: row[0] == ' '
                 for row in submodule_status.stdout.decode('utf8').split('\n') if len(row)}

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please run git 'submodule update --init --recursive'")


def run_make():
    print("Building libdatabase.so:")
    make_ret = subprocess.run(['make', 'OPTIMIZATION=-O3'])

    status("libdatabase.so", make_ret.returncode == 0)

    if (make_ret.returncode != 0):
        error("Make failed.")


def main():
    print("Search Engine Setup Coordinator")
    check_python_version()
    check_python_modules()
    check_system_packages()
    check_submodules()
    run_make()

if __name__ == "__main__":
    main()
