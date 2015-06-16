#!/bin/sh

mkdir client
echo $RANDOM | gpg --encrypt > client/test
