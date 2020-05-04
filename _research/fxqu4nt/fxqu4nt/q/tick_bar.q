\d .tickbar
bar:{[tb] ?[tb;();0b;`OpenBid`HighBid`LowBid`CloseBid`OpenAsk`HighAsk`LowAsk`CloseAsk`Volume`Start`End!((first;`Bid);(max;`Bid);(min;`Bid);(last;`Bid);(first;`Ask);(max;`Ask);(min;`Ask);(last;`Ask);(sum;`Volume);(first;`DateTime);(last;`DateTime))]}
totalTicks:{[z;b;e] count select from (z) where DateTime>=b, DateTime<(e+1)}
nsteps:{[sts;tt] (`int$tt%sts) + (?[mod[tt;sts]>0;1;0])}
nextOff:{[c;s;t;it] lc:last c;c,?[(lc+s)>t;t;lc+s]}
makeBars:{[ticktb;sts;bd;ed] /tableName, stepSize, beginDate, endDate, onMemory
    tot:totalTicks[ticktb;bd;ed];
    ns:nsteps[sts;tot];
    sl:enlist[0] nextOff[;sts;tot;]/til ns;
    tuol:sublist[(0;(count sl)-1);sl],'sublist[(1;count sl);sl];
    / table in memory use select, table in disk use .Q.ind
    bfn:{[z;x] $[not .Q.qp[z];select[(x[0];(x[1] - x[0]))] from z;.Q.ind[z;x[0]+til (x[1]-x[0])]]}[ticktb;];
    bsl:(bfn')tuol;
    (uj/)bar each (bsl (where ({(count x) > 0}) each bsl))}
dpt:{[d;tbn;t]
    alld:?[t;();1b;enlist[`Date]!enlist (`date$;`Start)]; / get all distinct start date
    p:?[;();();`Date]alld;
    tbyd: (enlist')(?[t;;0b;()]')(enlist')((=;($;enlist `date;`Start);)')p; / table by date
    (.cm.stb[d;tbn;1b]')p,'tbyd} 
genBars:{[d;tbn;qtb;sts] / symbolPath, tableName, quoteTable, stepSize
    fdate: .cm.fid[qtb];
    ldate: .cm.lad[qtb];
    ws: .cm.weeks[fdate;ldate];
    sfw: {[ztb;xsts;x] makeBars[ztb;xsts;x[0];x[1]]}[qtb;sts;];
    (dpt[d;"/",tbn,"/";]')(sfw')ws;
    system "l ",(d);
    neg[.z.w]("TASK_DONE");}
\d .