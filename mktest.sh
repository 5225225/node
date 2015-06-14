#!/usr/bin/sh

mkdir both client test
echo $RANDOM | gpg --encrypt --armor > both/test
echo $RANDOM | gpg --encrypt --armor > client/test
echo $RANDOM | gpg --encrypt --armor > server/test
