/ https://stackoverflow.com/questions/35347993/how-to-bulk-upsert-in-kdb
\d .quote / namespace for quote data storing utils
/ partition a table by `date$DateTime, see `.cm.stb` in utils/common.q
dpt:{[d;tbn;t] (.cm.stb[d;tbn]')p,'(enlist')(?[t;;0b;()]')(enlist')((=;($;enlist `date;`DateTime);)')p:?[;();();`Date]?[t;();1b;enlist[`Date]!enlist (`date$;`DateTime)]}
wqcsv:{[d;tbn] dpt[d;tbn]}
colnames:`DateTime`Bid`Ask`Volume
rqcsv:flip colnames!("ZFFI";",")0:
csvpt:{[d;f;tbn] .Q.fs[wqcsv[d;tbn] rqcsv@]hsym`$f}
tcsvpt:{[d;f;tbn]
    csvpt[d;f;"/",tbn,"/"];
    .dbmt.setattrcol[hsym`$d;`$tbn;`DateTime;`s]; /see utils/dbmaint.q
    system "l ",(d);
    neg[.z.w]("TASK_DONE");}
\d .