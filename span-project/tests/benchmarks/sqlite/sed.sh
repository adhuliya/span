#!/usr/bin/env bash


_STR="ERROR:Unknown";

sed -i "s/\x0//g" $1;
sed -i "s/${_STR}/expr.VarE('g:0d')/g" $1;

grep "$_STR" $1 | wc;
