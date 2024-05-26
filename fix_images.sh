#!/bin/bash

for i in ./output/images/*; do 
    ffmpeg -i $i -y -vf 'scale=if(gte(a\,800/800)\,min(800\,iw)\,-2):if(gte(a\,800/800)\,-2\,min(800\,ih))' $i; 
done