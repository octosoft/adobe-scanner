import sys
import os
from typing import Any, Dict

import yaml
import gzip
import time
import logging

# noinspection PyCompatibility
from pathlib import Path
from datetime import datetime, date
from optparse import OptionParser
from uuid import uuid1
from xml.dom.minidom import Document, Element

import umapi_client

# noinspection SpellCheckingInspection
octoscan_build = "adobe_scanner 1.10.0.30 - 2021-05-01"

# global config
config: Dict[Any, Any] = {}


def error_print(*args, **kwargs):
    """
    shortcut to print to stderr for fatal problems before logging is set up
    :param args:
    :param kwargs:
    """
    print(*args, file=sys.stderr, **kwargs)


def append_info_element(doc: Document, element: Element, name: str, info_type: str, value: str) -> None:
    """
        Appends an info element to the specified element in the xml document
        :param doc:
        :param element:
        :param name:
        :param info_type:
        :param value:
        :return:
        """
    assert isinstance(element, Element)
    info = doc.createElement("info")
    info.setAttribute("name", name)
    info.setAttribute("type", info_type)
    info.setAttribute("value", value)
    element.appendChild(info)


def append_dict(doc: Document, element: Element, d: {}) -> None:
    # noinspection SpellCheckingInspection
    """
            Appends a dictionary to the specified element in the xml document.
            This is a very trivial serialization of the dicts returned by the umapi queries

            :param doc:
            :param element:
            :param d:
            :return:

        """
    for key, value in d.items():
        if isinstance(value, str):
            append_info_element(doc, element, key, 'S', value)
        if isinstance(value, int):
            append_info_element(doc, element, key, 'I', str(value))
        if isinstance(value, list):
            list_element = doc.createElement(key)
            for i in value:
                item = doc.createElement('item')
                text = doc.createTextNode(i)
                item.appendChild(text)
                list_element.appendChild(item)
            element.appendChild(list_element)


def scan_umapi(log: logging.Logger, options: Any, output_folder: Path) -> None:
    """
            Call Adobe umapi and serialize results to compressed xml document
            :param log:
            :param options:
            :param output_folder:
            :return:
    """

    scanned_groups = 0
    scanned_users = 0

    org_id = config['org_id']

    # noinspection SpellCheckingInspection
    ext = ".scaa"
    output_file = output_folder.joinpath(options.uuid + ext)

    start_time = time.time()

    doc = Document()
    xml = doc.createElement('octoscan')
    xml.setAttribute("uuid", options.uuid)
    xml.setAttribute("timestamp", datetime.utcnow().replace(microsecond=0).isoformat())
    xml.setAttribute("build", octoscan_build)

    doc.appendChild(xml)

    octoscan_config = doc.createElement('octoscan_config')
    if len(options.tag) > 0:
        append_info_element(doc, octoscan_config, 'tag', 'S', options.tag)
    append_info_element(doc, octoscan_config, 'OutputFolder', 'S', str(output_folder))
    xml.appendChild(octoscan_config)

    meta = doc.createElement('meta')
    append_info_element(doc, meta, 'org_id', 'S', org_id)
    append_info_element(doc, meta, 'tech_acct_id', 'S', config['tech_acct_id'])
    xml.appendChild(meta)

    conn = None

    try:
        conn = umapi_client.Connection(org_id=org_id, auth_dict=config)
    except Exception as e:
        log.exception(e)

    if not conn:
        log.error("Failed to connect to Adobe cloud")

    groups = doc.createElement('groups')

    umapi_groups = umapi_client.GroupsQuery(conn)

    for umapi_group in umapi_groups:
        g = doc.createElement('group')
        g.setAttribute('name', umapi_group['groupName'])
        append_dict(doc, g, umapi_group)
        scanned_groups += 1
        groups.appendChild(g)

    xml.appendChild(groups)

    users = doc.createElement('users')
    umapi_users = umapi_client.UsersQuery(conn)

    for umapi_user in umapi_users:
        u = doc.createElement('user')
        u.setAttribute('name', umapi_user['username'])
        append_dict(doc, u, umapi_user)
        scanned_users += 1
        users.appendChild(u)

    xml.appendChild(users)

    end_time = time.time()

    performance = doc.createElement('octoscan_performance')
    append_info_element(doc, performance, 'seconds', 'I', str(int(end_time - start_time)))
    xml.appendChild(performance)

    with gzip.open(output_file, 'w') as f_out:
        f_out.write(doc.toprettyxml(indent="\t").encode('utf-8'))
        print(output_file)

    log.info(f"Adobe umapi {scanned_users} users {scanned_groups} groups scanned output to {output_file}")


# noinspection SpellCheckingInspection
def main():
    """
    Main function
    """
    global config
    parser = OptionParser()

    # noinspection SpellCheckingInspection
    parser.add_option("-o", "--outputfolder", dest="output_folder",
                      default=".",
                      help="write output file to specified directory")

    parser.add_option("-t", "--tag", dest="tag",
                      default="",
                      help="specify a tag that gets identify this specific scanner configuration")

    parser.add_option("-u", "--uuid", dest="uuid",
                      help="specify unique id to use",
                      default=str(uuid1()))

    parser.add_option("-l", "--log", dest="log_level",
                      help="specify loglevel to use",
                      default="INFO")

    parser.add_option("-c", "--config", dest="config_file",
                      help="specify configuration file to use",
                      default="")

    (options, args) = parser.parse_args()

    #
    # probe for configuration file outside current folder
    #
    # options --config or OCTOSAM_CONFIGURATION_FOLDER environment variables
    #

    if len(options.config_file):
        configuration_file = Path(options.config_file)
    else:
        configuration_file = Path("adobe_scanner_config.yaml")

        folder = os.environ.get("OCTOSAM_CONFIGURATION_FOLDER")
        if folder:
            config_folder = Path(folder)
            if config_folder.exists():
                probe = config_folder.joinpath(configuration_file)
                if probe.exists():
                    configuration_file = probe

    if not configuration_file.exists():
        error_print(f"IOError: {configuration_file}: no such file or directory")
        raise FileNotFoundError(f"Cannot find configuration file {configuration_file}")

    with open(configuration_file) as fin:
        config = yaml.safe_load(fin)

    if 'org_id' in config:
        org_id = config["org_id"]
    else:
        raise ValueError(f"Cannot read 'org_id' from config file {configuration_file}")

    log_file = None

    if 'log_folder' in config:
        log_folder = Path(config['log_folder'])
        if not log_folder.exists():
            error_print(f"IOError: {log_folder}: no such file or directory")
            exit(2)

        stamp = date.today().isoformat()
        log_file_name = f"adobe_scanner_{stamp}_log.txt"
        log_file = log_folder.joinpath(log_file_name)

    # create a logger
    log = logging.getLogger('adobe-scanner')
    numeric_level = getattr(logging, options.log_level.upper(), None)

    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.log_level)

    if log_file:
        logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                            filename=str(log_file),
                            level=numeric_level)
    else:
        logging.basicConfig(format='%(levelname)s - %(message)s',
                            level=numeric_level)

    log.info(f"Adobe umapi scanner started org: {org_id}")

    output_folder = Path(".")
    if 'output_folder' in config:
        output_folder = Path(config['output_folder'])

    if options.output_folder != ".":
        output_folder = Path(options.output_folder)

    if not output_folder.exists():
        msg = f"IOError: {options.output_folder}: no such file or directory"
        log.error(msg)
        error_print(msg)
        exit(2)

    if not output_folder.is_dir():
        msg = f"IOError: {options.output_folder}: not a directory"
        log.error(msg)
        error_print(msg)
        exit(2)

    try:
        scan_umapi(log, options, output_folder)
    except Exception as e:
        log.exception(e)


if __name__ == '__main__':
    main()
