# adobe-scanner

## Adobe Cloud Scanner for [OctoSAM Inventory](https://www.octosoft.ch)

## Basic Operation

The scan module for Adobe Cloud is a Python script.
The produced file has a .scaa extension.

### Installation

The current version of the scanner was tested with Python 3.8.7.
Install Python https://www.python.org/downloads/release/python-387/

Update pip and install the required python modules. 
The scanner uses the umapi-client for Python provided by Adobe which is distributed via 
python package repository. 

If you have other applications that use python on the same server, 
it's recommended that you create a virtual environment to install the required modules.

```shell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration

You need to register an integration on Adobe I/O via the Enterprise Dashboard
see https://adobe-apiplatform.github.io/umapi-client.py/

You need the following information to configure a the client connection

* Organization ID
* Tech Account ID
* API Key (sometimes referred to as Client ID in the docs)
* Client Secret
* Private Key File (unencrypted form)

Configure these values in adobe_scanner_config.yaml

### Invocation and Collection of Generated Files

```bash
python adobe_scanner.py
```

You are completely free on how to transfer the generated files to the OctoSAM Import Service import folder.
If you are running the scanner on windows, you can configure the collection share in adobe_scanner_config.yaml.
The files can also be uploaded via OctoCollect upload server running on Windows or Linux.

### Open File Format

The produced file is a zlib compressed .json file that contains all information as clear text

### Scanner Source License

The source code of the Adobe scanner is licensed under the MIT open source license. 
