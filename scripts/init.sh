#! /bin/bash
set -e

mkdir -p build
cd build

## Fetch a static ffmpeg build and put binaries into mp3-downloader/bin for dockerfile
mkdir -p ffmpeg
cd ffmpeg
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz.md5
md5sum -c ffmpeg-git-amd64-static.tar.xz.md5
tar xvf ffmpeg-git-amd64-static.tar.xz
mkdir -p ../../mp3-downloader/bin
mv ffmpeg-git-*-amd64-static/ffmpeg ffmpeg-git-*-amd64-static/ffprobe ../../mp3-downloader/bin
cd ..
cd ..
