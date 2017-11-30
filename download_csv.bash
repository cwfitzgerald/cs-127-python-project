#!/bin/bash

wget www.static.connorwfitzgerald.com/csv_cache --spider -r -P datasets

for i in $( find datasets -type f -name '*.tar.gz' ); do
	tar -xf $i -C .
	echo $i "->" ${i%%.*}.tar.gz
done

