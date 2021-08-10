for i in `ls *.csv`
do
	echo $i
	cut -f7 $i | sed '1,$s/,.*//'
done
