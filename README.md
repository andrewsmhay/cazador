# About Cazador
Cazador (Spanish for 'Hunter') is an open source and freely available tool to allow individuals to quickly determine if sensitive files and content are located in configured cloud environments. This information can be used in forensic and incident response activities, regulatory compliance assurance, and even for the creation of cyber threat intelligence (CTI) from one's own files to share with the security community.

## Supported Services

| Service             | Search by *md5* | Search by *sha1* | Search by *filename* |
| ------------------- |:---------------:|:----------------:|:--------------------:|
| **Amazon S3**       |               X^|                X^|                    X |
| **Box**             |                 |                X |                    X |
| **Dropbox**         |                 |                  |                    X |
| **Google Drive**    |               X |                  |                    X |

**^: Amazon S3 Hash searching will only detect files not uploaded using multipart uploads as multipart
uploads generates an random value for the file parts and reconstructed file's Etag field.**

## Installation

Note: This tool was developed using Python 3.5.x and will likely not work with 2.7.x.

Use Git or checkout with SVN using the web URL to install cazador:

```
$ git clone https://github.com/DataGravityInc/cazador.git
```

### Additional Libraries

Several libraries are required for cazador to function properly. These libraries include:

* apiclient
* boto3
* botocore
* bottle
* boxsdk
* docutils
* dropbox
* httplib2
* jmespath
* python-dateutil
* requests
* requests-toolbelt
* s3transfer
* six
* typing
* urllib3

Install the required helper libraries using `pip`

```
$ pip install -r requirements.txt
```

## Configuration

All cloud service configurations settings must be filled out in the `cloud.conf` file.

```python
[amazons3]
access_key_id =
secret_key =
region = us-east-1
buckets =

[dropbox]
access_token =

[box]
client_id =
client_secret =
local_auth_ip = localhost
local_auth_port = 8080

[googledrive]
client_id =
client_secret =
```

## Usage

```
$ python cazador.py -c <Config file> -s <Service Type>

    -s, --service= Cloud/File service type to search through.
                  !!! This must have a matching segment in the configuration document
    -c, --config= <Optional> File path to the configuration document for file/cloud service.
                  Default: [Current Directory]/cloud.conf
Known services:
    amazons3
    box
    dropbox
    googledrive
```

## Authors and Contributors
* Nathan Palmer, DataGravity, Inc. <a href="https://twitter.com/napalmer7">@napalmer7</a>
* Andrew Hay, DataGravity, Inc., <a href="https://twitter.com/andrewsmhay">@andrewsmhay</a>

## Support

Please submit all issues, questions, and feature requests using GitHub's _Issues_ section.

## License

The MIT License (MIT)

Copyright (c) 2016 DataGravity, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
