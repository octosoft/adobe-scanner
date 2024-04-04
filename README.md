# adobe-scanner

## Adobe cloud scanner for [OctoSAM Inventory](https://www.octosoft.ch)

## Basic operation

The OctoSAM Inventory scan module for Adobe Cloud is a Python script.
The produced file has a .scaa extension.

### Installation

The current version of the scanner was tested with Python 3.11.7

The recommended Python installation folder is c:\Python\Python311.
System-wide installation for all users is advised.

If you install Python in the user context,
you must consider the user context for invocation of the script - for example, from the OctoSAM Service Account.
There are many variants to installing and configuring Python on your machine.
This document covers only the most basic installation method.
If you have company-wide standards for Python installations, follow your standards.

Update pip and install the required Python modules.

The scanner uses the umapi-client for Python provided by Adobe, distributed via
Python package repository.

If you have other applications that use Python on the same server,
it's recommended that you create a virtual environment to install the required modules.
Virtual environment configuration is outside the scope of this document.

```shell
python -m pip install --upgrade pip
pip install -r d:/OctoSAM/Server/Scanners/adobe_scanner/requirements.txt
```

### Configuration

You need to register a project with UMAPI integration on Adobe Developer Console
see https://adobe-apiplatform.github.io/umapi-documentation/en/UM_Authentication.html

You need the following information to configure a client connection

* Organization ID
* Client ID
* Client Secret

Configure these values in adobe_scanner_config.yaml

You can also store the client secret in the windows credential manager by configuring the credential manager target.

The default configuration file name is %OCTOSAM_CONFIGURATION_FOLDER%\adobe_scanner_config.yaml

### Invocation and collection of generated files

```bash
python adobe_scanner.py --config d:\\MyConfigs\adobe_scanner_config.yaml
```

You may use any method to transfer the generated files to the OctoSAM Import Service import folder.
If you run the scanner on Windows, you can configure the collection share in adobe_scanner_config.yaml.
The files can also be uploaded via OctoSAM web-based upload server running on Windows or Linux.

### Open file format

The produced file is a zlib compressed XML file that contains all information as clear text.

### Scanner source license

The source code of the Adobe scanner is licensed under the MIT open-source license.
