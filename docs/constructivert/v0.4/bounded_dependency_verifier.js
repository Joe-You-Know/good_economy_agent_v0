/* ConstructiveRT bounded verification. Run: node bounded_dependency_verifier.js */
'use strict';
const fs = require('node:fs');
function experiment(){
 const joins=[
  {id:"A",ports:["p:L","q:T"],needs:[]},
  {id:"B",ports:["p:L","r:R"],needs:["X"]},
  {id:"C",ports:["q:B","r:L"],needs:[]},
  {id:"D",ports:["p:aux","r:aux"],needs:[]}
 ];
 const rule={when:["A","C"],then:"D"};
 const cases=[
  {name:"simultaneous_multipremise",facts:{X:"present"},positive:["A","C"],negative:[],history:[{id:"h1",orientation:"north"}]},
  {name:"alternative_proofs",facts:{X:"absent"},positive:["A","C"],negative:[],history:[{id:"h2",orientation:"north"}]},
  {name:"irrelevant_history_blue",facts:{X:"absent"},positive:["A","C"],negative:[],history:[{id:"extra",color:"blue",source:"s1"}]},
  {name:"irrelevant_history_red",facts:{X:"absent"},positive:["A","C"],negative:[],history:[{id:"extra",color:"red",source:"s1"}]},
  {name:"underdetermined",facts:{X:"unknown"},positive:[],negative:[],history:[{id:"h3",orientation:"unknown"}]},
  {name:"contradictory_reports",facts:{X:"present"},positive:["A"],negative:["A"],history:[{id:"conflict",reports:["A+","A-"]}]}
 ];
 function reference(c){
  if(c.positive.some(x=>c.negative.includes(x)))return {status:"conflict",modelCount:0,materialized:0,examined:0};
  const accepted=[];let examined=0,materialized=0;
  for(let mask=0;mask<(1<<joins.length);mask++){
   examined++;
   const realized=joins.filter((_,i)=>mask&(1<<i)).map(j=>{materialized++;return {joinId:j.id,participants:j.ports.slice(),hypothetical:true};});
   const selected=new Set(realized.map(x=>x.joinId));
   if(c.positive.some(x=>!selected.has(x))||c.negative.some(x=>selected.has(x)))continue;
   if(realized.some(r=>joins.find(j=>j.id===r.joinId).needs.some(t=>c.facts[t]==="absent")))continue;
   const ports=realized.flatMap(x=>x.participants);
   if(new Set(ports).size!==ports.length)continue;
   if(rule.when.every(x=>selected.has(x))&&!selected.has(rule.then))continue;
   accepted.push(selected);
  }
  if(!accepted.length)return {status:"inconsistent",modelCount:0,examined,materialized};
  const entailedYes=joins.filter(j=>accepted.every(m=>m.has(j.id))).map(j=>j.id);
  const entailedNo=joins.filter(j=>accepted.every(m=>!m.has(j.id))).map(j=>j.id);
  return {status:"ok",modelCount:accepted.length,entailedYes,entailedNo,examined,materialized};
 }
 function direct(c){
  if(c.positive.some(x=>c.negative.includes(x)))return {status:"conflict",proofs:{},forcedYes:[],forcedNo:[],hypotheticalSuccessObjects:0,steps:0};
  const yes=new Set(c.positive),no=new Set(c.negative),proofs={};let steps=0;
  for(const a of c.positive)proofs["+"+a]=[["witness:"+a]];
  for(const a of c.negative)proofs["-"+a]=[["negative_witness:"+a]];
  let change=true,rounds=0;
  while(change){
   if(++rounds>8)throw Error("unexpected cycle");change=false;
   for(const j of joins){
    const reasons=[];
    for(const t of j.needs)if(c.facts[t]==="absent")reasons.push(["absent_original_property:"+t]);
    for(const k of joins){
     if(k.id!==j.id && yes.has(k.id) && k.ports.some(p=>j.ports.includes(p)))reasons.push(["witnessed_join:"+k.id,"shared_port:"+k.ports.find(p=>j.ports.includes(p))]);
    }
    if(reasons.length){
     steps+=reasons.length;
     if(yes.has(j.id))return {status:"conflict",proofs,forcedYes:[],forcedNo:[],hypotheticalSuccessObjects:0,steps};
     if(!no.has(j.id)){no.add(j.id);change=true;}
     proofs["-"+j.id]=reasons;
    }
   }
   if(rule.when.every(x=>yes.has(x))){steps++;if(no.has(rule.then))return {status:"conflict",proofs,forcedYes:[],forcedNo:[],hypotheticalSuccessObjects:0,steps};if(!yes.has(rule.then)){yes.add(rule.then);change=true;proofs["+"+rule.then]=[rule.when.map(x=>"witnessed_join:"+x).concat("law:joint_obligation")];}}
  }
  return {status:"ok",forcedYes:[...yes].sort(),forcedNo:[...no].sort(),proofs,steps,hypotheticalSuccessObjects:0};
 }
 const report=[];
 for(const c of cases){
  const before=JSON.stringify(c),d=direct(c),o=reference(c); const recovered=JSON.parse(before);
  const exact=JSON.stringify(recovered)===before&&JSON.stringify(c)===before;
  if(!exact)throw Error("ledger mismatch "+c.name);
  if(d.status!==o.status)throw Error("status mismatch "+c.name+" "+d.status+"/"+o.status);
  if(o.status==="ok"&&(d.forcedYes.some(x=>!o.entailedYes.includes(x))||d.forcedNo.some(x=>!o.entailedNo.includes(x))))throw Error("unsound direct "+c.name);
  report.push({case:c.name,oracleModels:o.modelCount,oracleMaterialized:o.materialized,oracleEnumerated:o.examined,directHypotheticalObjects:d.hypotheticalSuccessObjects,directSteps:d.steps,yes:d.forcedYes,no:d.forcedNo,oracleYes:o.entailedYes,oracleNo:o.entailedNo,proofs:d.proofs,exact});
 }
 const a=report.find(x=>x.case==="alternative_proofs");
 if((a.proofs["-B"]||[]).length!==2)throw Error("missing alternative proofs");
 if(!report.find(x=>x.case==="simultaneous_multipremise").yes.includes("D"))throw Error("missing joint obligation");
 if(report[2].yes.join()!=report[3].yes.join()||report[2].no.join()!=report[3].no.join())throw Error("irrelevant history affected conclusion");
 if(cases[2].history[0].color===cases[3].history[0].color)throw Error("history collision");
 return {report,joins,rule,cases};
}
const out=experiment();
console.log(JSON.stringify(out.report,null,2));
