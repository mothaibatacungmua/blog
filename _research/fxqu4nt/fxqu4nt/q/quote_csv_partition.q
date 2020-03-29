/ https://stackoverflow.com/questions/35347993/how-to-bulk-upsert-in-kdb
isPathExist:{[d] not (() ~ key hsym`$d)}
stb:{[d;tbn;zpt]
    sd:(d,"/",string zpt[0]),tbn;
    $[isPathExist[sd];(hsym`$sd) upsert zpt[1];(hsym`$sd) set .Q.en[hsym`$d;zpt[1]]];
    neg[.z.w](enlist[`processed]! enlist string zpt[0]);}
dpt:{[d;tbn;t] (stb[d;tbn]')p,'(enlist')(?[t;;0b;()]')(enlist')((=;($;enlist `date;`DateTime);)')p:?[;();();`Date]?[t;();1b;enlist[`Date]!enlist (`date$;`DateTime)]}

wqcsv:{[d;tbn] dpt[d;tbn]}
colnames:`DateTime`Bid`Ask`Volume
rqcsv:flip colnames!("ZFFI";",")0:

csvpt:{[d;f;tbn] .Q.fs[wqcsv[d;tbn] rqcsv@]hsym`$f}
tcsvpt:{[d;f;tbn]
    csvpt[d;f;"/",tbn,"/"];
    setattrcol[hsym`$d;`$tbn;`DateTime;`s]; /see utils/dbmaint.q
    system "l ",(d);
    neg[.z.w]("TASK_DONE");}