#!/bin/bash

for i in $( find datasets -type f -name '*.csv' ); do
	echo $i "->" ${i%%.*}.tar.gz
	tar zcvf ${i%%.*}.tar.gz $i
done

rsync -ah --progress $( find datasets -type f -name '*.tar.gz' ) connor@static.connorwfitzgerald.com:/home/connor/static_data/csv_cache/
