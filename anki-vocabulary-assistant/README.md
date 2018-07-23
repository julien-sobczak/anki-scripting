# Anki Vocabulary Assistant

## Building

To build the Docker image:

```
$ docker build -t assistant .
```

## Running

To run the Docker image locally:

```
$ docker run -p 80:8080 -d --name assistant -v save:/save -e "DEVELOP_KEY=<your_developer_key>" -e "CX=<your_cx>" assistant
```

Browse to: http://localhost
