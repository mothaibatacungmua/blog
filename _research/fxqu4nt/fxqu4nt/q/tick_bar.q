\d .tickbar
bar:{[tb;pt] ?[tb;();0b;`Open`High`Low`Close`Volume`Start`End!((first;pt);(max;pt);(min;pt);(last;pt);(sum;`Volume);(first;`DateTime);(last;`DateTime))]}
totalTicks:{[z;b;e] count select from (z) where DateTime>=b, DateTime<e}
nsteps:{[sts;tt] (`int$tt%sts) + (?[mod[tt;sts]>0;1;0])}
nextOff:{[c;s;t;it] lc:last c;c,?[(lc+s)>t;t;lc+s]}
makeBars:{[ticktb;pt;sts;bd;ed] /tableName, priceType, stepSize, beginDate, endDate
	tot:totalTicks[ticktb;bd;ed];
	ns:nsteps[sts;tot];
	sl:enlist[0] nextOff[;sts;tot;]/til ns;
	tuol:sublist[(0;(count sl)-1);sl],'sublist[(1;count sl);sl];
	bfn:{[z;x] .Q.ind[z;x[0]+til (x[1]-x[0])]}[ticktb;];
	bsl:(bfn')tuol;
	(uj/)bar[;pt] each (bsl (where ({(count x) > 0}) each bsl))}
\d .