## Build docker image
```
docker build . -t kikit-rezonit:v1.3.0-v7
```

## Run terminal in docker
- Run this cmd from pcb kicad project folder
- Current project folder mount to `/prj`
#### Windows
```
docker run -it -v %cd%:/prj kikit-rezonit:v1.3.0-v7
```
#### MAC
```
docker run -it -v $(pwd):/prj kikit-rezonit:v1.3.0-v7
```

## Save image to tar
```
docker save --output="kikit-rezonit-1.3.0-v7.tar" kikit-rezonit:v1.3.0-v7
```
