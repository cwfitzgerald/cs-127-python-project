#!/bin/bash

wget www.static.connorwfitzgerald.com/csv_cache/{offenders.tar.gz,gutenberg.tar.gz} -P datasets -nc

for i in $( find datasets -type f -name '*.tar.gz' ); do
	tar -xf $i -C .
	echo $i "->" ${i%%.*}.csv
done

