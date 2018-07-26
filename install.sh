#!/bin/bash

HUB_VERSION_NUMBER="2.5.0"

# Install hub (https://github.com/github/hub)
wget https://github.com/github/hub/releases/download/v${HUB_VERSION_NUMBER}/hub-linux-amd64-${HUB_VERSION_NUMBER}.tgz
tar zvxvf hub-linux-amd64-${HUB_VERSION_NUMBER}.tgz
sudo ./hub-linux-amd64-${HUB_VERSION_NUMBER}/install
rm -rf hub-linux-amd64-${HUB_VERSION_NUMBER}.tgz
