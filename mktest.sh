#!/usr/bin/sh

mkdir both client server
echo $RANDOM | gpg --encrypt > both/test
echo $RANDOM | gpg --encrypt > client/test
echo $RANDOM | gpg --encrypt > server/test
