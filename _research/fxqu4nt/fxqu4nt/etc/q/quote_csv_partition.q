
stb:{[d;zpt] sd:(d,"/",string zpt[0]),"/quote/";(hsym`$sd) set .Q.en[hsym`$d;zpt[1]]}
dpt:{[d;t] (stb[d;]')p,'(enlist')(?[t;;0b;()]')(enlist')((=;($;enlist `date;`DateTime);)')p:?[;();();`Date]?[t;();1b;enlist[`Date]!enlist (`date$;`DateTime)]}

w:{[d] dpt[d;]}
colnames:`DateTime`Bid`Ask`Volume
r:flip colnames!("ZFFI";",")0:

csvpt:{[d;f] .Q.fs[w[d] r@]hsym`$f}
