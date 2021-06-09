# cert-retriever

This image contains a Python script which gets a list of all the AWS ACM certificates and retrieves them, 
saving them in the path specified using `CERTS_DESTINATION_FOLDER`.

## Docker repository for fetching all ACM certs in different environmentsg

This repo contains Makefile, and Dockerfile to fit the standard pattern. This repo is a base to create new Docker image
repos, adding the githooks submodule, making the repo ready for use.

After cloning this repo, please run:  
`make bootstrap`

## Environment variables

The required environment variables. They are replaced with the parameters passed in from the above arguments
* The `CERTS_DESTINATION_FOLDER` is needed or the script will fail to execute

|      Variable name       | Example       | Description                                          |
|--------------------------|:-------------:|-----------------------------------------------------:|
| CERTS_DESTINATION_FOLDER | /certificates | The path in which pulled certificates will be placed |
| LOG_LEVEL                | INFO          | The desired log level, INFO or DEBUG                 |
| ENVIRONMENT              | NOT_SET       | The environment the app runs in. e.g. Development    |
| APPLICATION              | NOT_SET       | The name of the application                          |
