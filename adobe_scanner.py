import sys
import os
import yaml
import json
import gzip

# noinspection PyCompatibility
from pathlib import Path
from datetime import datetime
from optparse import OptionParser
from uuid import uuid1

import umapi_client


def error_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def main():
    parser = OptionParser()

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
            error_print("IOErrror: " + options.output_folder + ": not a directory")
            exit(2)

        output_file = output_folder.joinpath(options.uuid + ext)

        conn = umapi_client.Connection(org_id=config["org_id"], auth_dict=config)

        groups = umapi_client.GroupsQuery(conn)

        meta = {'created': datetime.now().isoformat()}

        o_groups = []
        o_users = []

        # print all the group details
        for group in groups:
            o_groups.append(group)

        users = umapi_client.UsersQuery(conn)
        for user in users:
            o_users.append(user)

        data = {'meta': meta, 'groups': o_groups, 'users': o_users}

        with gzip.open(output_file, 'w') as fout:
            fout.write(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))

            print(output_file)


if __name__ == '__main__':
    main()
