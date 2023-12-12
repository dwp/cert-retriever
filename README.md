# DO NOT USE THIS REPO - MIGRATED TO GITLAB

# cert-retriever

This image contains a Python script which gets a list of all the AWS ACM and retrieves them, 
saving them in the path specified using `CERTS_DESTINATION_FOLDER`. Additionally, the script reads some non-ACM certificates stored in the S3 bucket `ADDITIONAL_CERTS_BUCKET` at any of the paths and any of the folders within the path(s) specified in the `ADDITIONAL_CERTS_PREFIXES` and saves them in the destination folder along with the ACM certificates.

## Docker repository for fetching all ACM certs in different environments

This repo contains Makefile, and Dockerfile to fit the standard pattern. This repo is a base to create new Docker image
repos, adding the githooks submodule, making the repo ready for use.

After cloning this repo, please run:  
`make bootstrap`

## Environment variables

The required environment variables. They are replaced with the parameters passed in from the above arguments
* The `CERTS_DESTINATION_FOLDER` is needed or the script will fail to execute

|      Variable name        | Example              | Description                                          |
|---------------------------|:--------------------:|-----------------------------------------------------:|
| CERTS_DESTINATION_FOLDER  | /certificates        | The path in which pulled certificates will be placed |
| LOG_LEVEL                 | INFO                 | The desired log level, INFO or DEBUG                 |
| ENVIRONMENT               | NOT_SET              | The environment the app runs in. e.g. Development    |
| APPLICATION               | NOT_SET              | The name of the application                          |
| ADDITIONAL_CERTS_BUCKET   | bucket-name          | The id of the S3 bucket where non-ACM certs are      |
| ADDITIONAL_CERTS_PREFIXES | ab_certs,cd/ef_certs | The string of comma separated prefixes               |
