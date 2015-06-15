#!/usr/bin/sh

mkdir both client test
echo $RANDOM | gpg --encrypt > both/test
echo $RANDOM | gpg --encrypt > client/test
echo $RANDOM | gpg --encrypt > server/test
