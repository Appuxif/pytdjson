# Ubuntu20 tdlib


## Build Image
> source .env
> sudo docker login -u $DOCKER_USERNAME -p $DOCKER_API_KEY
> sudo docker build . -t $DOCKER_USERNAME/ubuntu24tdlib:latest -t $DOCKER_USERNAME/ubuntu24tdlib:1.8.56
> sudo docker push $DOCKER_USERNAME/ubuntu24tdlib:latest $DOCKER_USERNAME/ubuntu24tdlib:1.8.56

## Build tdlib
> sudo docker compose up --build --force-recreate build-tdlib


## Build generator
https://tdlib.github.io/td/build.html?language=Python

> Choose a programming language from which you want to use TDLib:
> Python
> 
> Choose an operating system on which you want to use TDLib:
> Linux
> 
> Choose a Linux distro on which you want to use TDLib:
> Ubuntu 24.04
> 
> Choose which compiler you want to use to build TDLib:
> g++
> 

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install make git zlib1g-dev libssl-dev gperf php-cli cmake g++
git clone https://github.com/tdlib/td.git
cd td
rm -rf build
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=../tdlib ..
cmake --build . --target install
cd ..
cd ..
ls -l td/tdlib
```
