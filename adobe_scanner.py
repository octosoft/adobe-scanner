import sys
import os
import yaml
import gzip

# noinspection PyCompatibility
from pathlib import Path
from datetime import datetime
from optparse import OptionParser
from uuid import uuid1
from xml.dom.minidom import Document, Element

import umapi_client

# noinspection SpellCheckingInspection
octoscan_build = "adobe_scanner 1.10.0.0 - 2021-02-20"


def error_print(*args, **kwargs):
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


# noinspection SpellCheckingInspection
def main():
    parser = OptionParser()

    # noinspection SpellCheckingInspection
    parser.add_option("-o", "--outputfolder", dest="output_folder",
                      default=".",
                      help="write output file to specified directory")

    parser.add_option("-u", "--uuid", dest="uuid",
                      help="specify unique id to use",
                      default=str(uuid1()))

    (options, args) = parser.parse_args()

    #
    # probe for configuration file outside current folder
    #
    configuration_file = Path("adobe_scanner_config.yaml")

    folder = os.environ.get("OCTOSAM_CONFIGURATION_FOLDER")
    if folder:
        config_folder = Path(folder)
        if config_folder.exists():
            probe = config_folder.joinpath(configuration_file)
            if probe.exists():
                configuration_file = probe

    with open(configuration_file) as fin:
        config = yaml.safe_load(fin)

        org_id = config["org_id"]

        output_folder = Path(".")
        if 'output_folder' in config:
            output_folder = Path(config['output_folder'])

        if options.output_folder != ".":
            output_folder = Path(options.output_folder)

        ext = ".scaa"

        if not output_folder.exists():
            error_print("IOError: " + options.output_folder + ": no such file or directory")
            exit(2)

        if not output_folder.is_dir():
            error_print("IOError: " + options.output_folder + ": not a directory")
            exit(2)

        output_file = output_folder.joinpath(options.uuid + ext)

        doc = Document()
        xml = doc.createElement('octoscan')
        xml.setAttribute("uuid", options.uuid)
        xml.setAttribute("timestamp", datetime.utcnow().replace(microsecond=0).isoformat())
        xml.setAttribute("build", octoscan_build)

        doc.appendChild(xml)

        meta = doc.createElement('meta')
        append_info_element(doc, meta, 'org_id', 'S', org_id)
        append_info_element(doc, meta, 'tech_acct_id', 'S', config['tech_acct_id'])
        xml.appendChild(meta)

        conn = umapi_client.Connection(org_id=org_id, auth_dict=config)

        groups = doc.createElement('groups')

        umapi_groups = umapi_client.GroupsQuery(conn)

        for umapi_group in umapi_groups:
            g = doc.createElement('group')
            g.setAttribute('id', str(umapi_group['groupId']))
            g.setAttribute('name', umapi_group['groupName'])
            append_dict(doc, g, umapi_group)
            groups.appendChild(g)

        xml.appendChild(groups)

        users = doc.createElement('users')
        umapi_users = umapi_client.UsersQuery(conn)

        for umapi_user in umapi_users:
            u = doc.createElement('user')
            u.setAttribute('name', umapi_user['username'])
            append_dict(doc, u, umapi_user)
            users.appendChild(u)

        xml.appendChild(users)

        with gzip.open(output_file, 'w') as fout:
            fout.write(doc.toprettyxml(indent="\t").encode('utf-8'))
            print(output_file)


if __name__ == '__main__':
    main()
