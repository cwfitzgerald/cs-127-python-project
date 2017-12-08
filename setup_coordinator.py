#!/usr/bin/env python3

import argparse
import corelib.add_dataset
import corelib.database_interface as db
import corelib.util as util
import enum
import json
import os
import subprocess
import sys
import tarfile

python_modules_needed = ['anytree', 'flask', 'cachetools']
packages_needed_osx = ['sqlite', 'icu4c']
packages_needed_linux = ['libsqlite3-dev', 'libicu-dev', 'make', 'g++']


def section_title(title):
    print("\u001b[37;1m{}\u001b[0m".format(title))


def status(name, success):
    print("\t{} -- {}".format(name, "\u001b[32;1mSuccess\u001b[0m" if success else "\u001b[31;1mFailure\u001b[0m"))


def error(text):
    print("\u001b[31;1mERROR:\u001b[0m {}".format(text))
    exit(1)


def check_python_version():
    section_title("Checking python version:")

    success = sys.version_info.major == 3 and sys.version_info.minor >= 5
    name = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    status(name, success)

    if (not success):
        error("Please install Python 3.5 or greater")


def check_python_modules():
    section_title("Checking python modules:")

    successes = {}
    for module in python_modules_needed:
        successes[module] = subprocess.run([sys.executable, '-c', 'import {}'.format(module)],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please run 'pip3 install {}'".format(" ".join([name for name, result in successes.items()
                                                             if not result])))


def check_system_packages():
    if sys.platform.startswith('linux'):
        _check_system_packages_linux()
    elif sys.platform.startswith('darwin'):
        _check_system_packages_osx()


def _check_system_packages_linux():
    section_title("Checking system packages:")
    dpkg_query = subprocess.run(['dpkg-query', '--list'], stdout=subprocess.PIPE)

    names = [row.split()[1].partition(':')[0]
             for row in dpkg_query.stdout.decode('utf8').split('\n')[5:] if len(row) >= 2]

    successes = {package: package in names for package in packages_needed_linux}

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please run 'sudo apt install {}'".format(" ".join([name for name, result in successes.items()
                                                                  if not result])))


def _check_system_packages_osx():
    section_title("Checking system packages:")
    brew_query = subprocess.run(['brew', 'list'], stdout=subprocess.PIPE)

    names = [row for row in brew_query.stdout.decode('utf8').split('\n')]

    successes = {package: package in names for package in packages_needed_osx}

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please run 'brew install {}'".format(" ".join([name for name, result in successes.items()
                                                              if not result])))


def check_submodules():
    section_title("Checking submodules:")
    submodule_status = subprocess.run(['git', 'submodule', 'status', '--recursive'], stdout=subprocess.PIPE)

    successes = {row.split()[1]: row[0] == ' '
                 for row in submodule_status.stdout.decode('utf8').split('\n') if len(row)}

    for name, result in sorted(successes.items()):
        status(name, result)

    if (False in successes.values()):
        error("Please run 'git submodule update --init --recursive'")


def run_make():
    section_title("Building all code:")

    if (sys.platform.startswith("darwin")):
        brew_prefixes = [subprocess.run(['brew', '--prefix', lib],
                                        stdout=subprocess.PIPE).stdout.decode('utf8').replace('\n', ' ')
                         for lib in packages_needed_osx]

        brew_includes = ["-isystem " + os.path.join(prefix, "include") for prefix in brew_prefixes]
        brew_links = ["-L" + os.path.join(prefix, "lib") for prefix in brew_prefixes]

        extraflags = " ".join(brew_includes) + " " + " ".join(brew_links)
    else:
        extraflags = ""

    make_ret = subprocess.run(['make', 'OPTIMIZATION=-O3', 'EXTRAFLAGS={}'.format(extraflags)])

    status("libdatabase.so", make_ret.returncode == 0)

    if (make_ret.returncode != 0):
        error("Make failed.")


class CSVStatus(enum.Enum):
    OK = 1
    MISSING = 2
    ZIPPED = 3
    IGNORE = 4
    INDB = 5


def print_csv_status(name, status):
    if (status == CSVStatus.OK):
        status_msg = "\u001b[32;1mFound"
    elif (status == CSVStatus.INDB):
        status_msg = "\u001b[32;1mIn Database"
    elif (status == CSVStatus.MISSING):
        status_msg = "\u001b[31;1mMissing"
    elif (status == CSVStatus.ZIPPED):
        status_msg = "\u001b[33;1mZipped"
    elif (status == CSVStatus.IGNORE):
        status_msg = "\u001b[31mToo Big"

    print("\t{} -- {}\u001b[0m".format(name, status_msg))


def check_list_of_csvs(mb_limit):
    section_title("Checking status of CSVs")

    byte_limit = 1024 * 1024 * mb_limit

    settings = json.load(open("datasets/index.json"))

    csvs = [os.path.basename(file) for file in os.listdir("datasets") if file.endswith(".csv")]
    tars = [os.path.basename(file)[:-7] for file in os.listdir("datasets") if file.endswith(".tar.gz")]

    res = {}
    for csv in settings:
        if mb_limit != 0 and settings[csv]["size"] > byte_limit:
            res[csv] = CSVStatus.IGNORE
        elif db.data_rows(csv) != 0:
            res[csv] = CSVStatus.INDB
        elif csv not in csvs:
            tar_wo_extent = os.path.splitext(csv)[0]
            tar_full_path = os.path.join("datasets/", tar_wo_extent + ".tar.gz")
            tar_usable = (tar_wo_extent in tars) and (os.stat(tar_full_path).st_size == settings[csv]["tar_size"])

            res[csv] = CSVStatus.ZIPPED if tar_usable else CSVStatus.MISSING
        else:
            res[csv] = CSVStatus.OK

    for name, result in res.items():
        print_csv_status(name, result)

    return res


def download_csv(csv_list):
    if CSVStatus.MISSING not in csv_list.values():
        return

    section_title("Downloading CSVs:")

    prefix = 'www.static.connorwfitzgerald.com/csv_cache/'

    files = [prefix + os.path.splitext(name)[0] + ".tar.gz"
             for name, status in csv_list.items()
             if status == CSVStatus.MISSING]
    wget = subprocess.run(['wget', '--continue', '-q', '--show-progress', '-P', 'datasets' '', *files])

    for name, result in csv_list.items():
        if result == CSVStatus.MISSING:
            csv_list[name] = CSVStatus.ZIPPED
            status(name, True)


def unzip_csv(csv_list):
    if CSVStatus.ZIPPED not in csv_list.values():
        return

    section_title("Unzipping CSVs:")

    for name, status in csv_list.items():
        if status == CSVStatus.ZIPPED:
            sys.stdout.write("\t{}... ".format(name))
            sys.stdout.flush()
            tar_loc = os.path.join("datasets/", os.path.splitext(name)[0] + ".tar.gz")

            file = tarfile.open(tar_loc, 'r')

            file.extractall(".")

            csv_list[name] = CSVStatus.OK

            print("\u001b[32;1mSuccess\u001b[0m")


def csv_cull(csv_list):
    return {name: status for name, status in csv_list.items() if status in (CSVStatus.OK, CSVStatus.INDB)}


def build_data_table(csv_list):
    if (CSVStatus.OK not in csv_list.values()):
        return

    section_title("Adding CSVs to database:")

    corelib.add_dataset.add_csv_to_database([os.path.join("datasets/", name)
                                             for name, status in csv_list.items()
                                             if status == CSVStatus.OK],
                                            delete=True)

    for name, status in csv_list.items():
        if status == CSVStatus.OK:
            csv_list[name] = CSVStatus.INDB


def build_iindex_tables(csv_list):
    csv_need_insertion = [db.iindex_rows(name) == 0 for name in csv_list]

    if not any(csv_need_insertion):
        return

    section_title("Building iindex tables:")

    for name, insert in zip(csv_list, csv_need_insertion):
        if insert:
            db.build_iindex_database(name)


def remove_file(name, exists=None):
    if (exists is None):
        exists = os.path.isfile(name)
    if (exists):
        os.remove(name)

    print("\t{} -- {}".format(os.path.relpath(name),
                              "\u001b[32;1mSuccess\u001b[0m" if exists else "\u001b[31;1mDoesn't Exist\u001b[0m"))


def clean_code():
    section_title("Cleaning All Code:")

    remove_file(util.relative_path(__file__, "corelib/libdatabase.so"))


def clean_db():
    section_title("Cleaning Database:")

    db_path = util.relative_path(__file__, "datasets/datasets.sql")
    if (os.stat(db_path).st_size != 0):
        remove_file(db_path)
    else:
        remove_file(db_path, False)
    remove_file(util.relative_path(__file__, "datasets/translations.json"))


def clean_downloads():
    section_title("Cleaning Downloaded Files:")

    csvs = [file for file in os.listdir("datasets") if file.endswith(".csv")]
    tars = [file for file in os.listdir("datasets") if file.endswith(".tar.gz")]

    for csv in csvs:
        remove_file(os.path.join("datasets/", csv))
    for tar in tars:
        remove_file(os.path.join("datasets/", tar))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', help="Build database and all code (default)", action="store_true")
    parser.add_argument('--build-code', help="Build all code (default)", action="store_true")
    parser.add_argument('--clean', '--clean-db', help="Remove the database", action="store_true")
    parser.add_argument('--clean-code', help="Clean all code", action="store_true")
    parser.add_argument('--clean-downloads', help="Clean all downloaded/unpacked files", action="store_true")
    parser.add_argument('--clean-all', help="Clean EVERYTHING", action="store_true")
    parser.add_argument('--download', help="Download csvs", action="store_true")
    parser.add_argument('--max', '--max-csv-size',
                        help="Maximum csv size in megabytes to add to database, 0 for none: (default 200",
                        type=float, default=100)
    arguments = parser.parse_args()

    maxsize = arguments.max

    flag_build_code = False
    flag_build_db = False
    flag_clean_code = False
    flag_clean_db = False
    flag_clean_downloads = False
    flag_download = False

    if (arguments.build_code):
        flag_build_code = True
    if (arguments.clean):
        flag_clean_db = True
    if (arguments.clean_code):
        flag_clean_code = True
    if (arguments.clean_downloads):
        flag_clean_downloads = True
    if (arguments.clean_all):
        flag_clean_db = True
        flag_clean_code = True
        flag_clean_downloads = True
    if (arguments.download):
        flag_download = True
    if (arguments.build or not any([flag_build_code, flag_build_db, flag_clean_code,
                                    flag_clean_db, flag_clean_downloads, flag_download])):
        flag_build_code = True
        flag_download = True
        flag_build_db = True

    section_title("Search Engine Setup Coordinator")
    check_python_version()
    if (flag_clean_downloads):
        clean_downloads()
    if (flag_clean_db):
        clean_db()
    if (flag_clean_code):
        clean_code()

    if (flag_build_code):
        check_python_modules()
        check_system_packages()
        check_submodules()
        run_make()

    if (flag_download or flag_build_db):
        csv_list = check_list_of_csvs(maxsize)

    if (flag_download):
        download_csv(csv_list)
        unzip_csv(csv_list)

    if (flag_build_db):
        csv_list = csv_cull(csv_list)
        build_data_table(csv_list)
        build_iindex_tables(csv_list)
        section_title("Database built - ready for use")

    print("\u001b[32;1mComplete!\u001b[0m")


if __name__ == "__main__":
    main()
