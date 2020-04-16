\d .cm
/ date common utils
weeks: {[st; et] / generate 
    sd: `date$st; ed: `date$et;
    fm: 2 + sd - sd mod 7;
    ls: 6 + ed - ed mod 7;
    alld: fm + til (1 + ls - fm);
    mons: alld where ({2=x mod 7}) each alld;
    fris: alld where ({6=x mod 7}) each alld;
    mons,'fris}

/ file common utils
isPathExist:{[d] not (() ~ key hsym`$d)} / check a file path exist

/ db common utils
stb:{[d;tbn;zpt] 
    / upsert a table to a directory by date
    sd:(d,"/",string zpt[0]),tbn;
    $[isPathExist[sd];(hsym`$sd) upsert zpt[1];(hsym`$sd) set .Q.en[hsym`$d;zpt[1]]];
    neg[.z.w](enlist[`processed]! enlist string zpt[0]);}
\d .