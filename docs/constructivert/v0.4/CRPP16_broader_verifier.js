'use strict';
// CRPP-16 reproducible broader benchmark. Node 18+, standard library only.
const assert=require('node:assert/strict'),crypto=require('node:crypto'),zlib=require('node:zlib');
const {performance}=require('node:perf_hooks');
const G={joins:[
{id:'A',ports:['p:x','q:a'],needs:[]},{id:'B',ports:['p:x','r:b'],needs:['X']},
{id:'C',ports:['q:c','r:d'],needs:[]},{id:'D',ports:['p:u','s:e'],needs:[]},
{id:'E',ports:['r:v','t:f'],needs:['Y']},{id:'F',ports:['t:g','u:h'],needs:[]},
{id:'G',ports:['s:i','u:j'],needs:[]},{id:'H',ports:['p:z','u:k'],needs:[]},
{id:'I',ports:['r:w','s:l'],needs:[]},{id:'J',ports:['t:m','q:n'],needs:[]}],
implications:[{when:['A','C'],then:'D'},{when:['D','F'],then:'G'},
{when:['E','H'],then:'I'},{when:['B','F'],then:'J'}]};
const IDS=G.joins.map(j=>j.id),JOIN=Object.fromEntries(G.joins.map(j=>[j.id,j]));
const encode=x=>Buffer.from(JSON.stringify(x),'utf8');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function makeCase(i){
 const status=['present','absent','unknown'];
 const facts={X:status[i%3],Y:status[Math.floor(i/3)%3]};
 let positive=[],negative=[];const selected=IDS[i%10];
 if(i%5===0)positive=[selected];
 if(i%7===0)negative=[IDS[(i+3)%10]];
 if(i%31===0)positive=['A','C'];
 if(i%41===0)positive=['D','F'];
 if(i%47===0)positive=['E','H'];
 if(i%53===0)positive=['B','F'];
 if(i%67===0)negative=[...negative,...positive.slice(0,1)];
 return {caseId:'case-'+String(i).padStart(4,'0'),facts,positive,negative,
 history:[{event:'contact',source:'source-'+(i%9),orientation:i%2?'cw':'ccw',remark:'unrelated-'+i,rawWitness:['alpha','beta',i]}]};
}
function cases(){
 return [...Array.from({length:240},(_,i)=>makeCase(i)),
 {caseId:'alt-proofs',facts:{X:'absent',Y:'unknown'},positive:['A'],negative:[],history:[{source:'alt',irrelevant:'a'}]},
 {caseId:'ledger-blue',facts:{X:'absent',Y:'unknown'},positive:['A','C'],negative:[],history:[{source:'same',irrelevant:'blue'}]},
 {caseId:'ledger-red',facts:{X:'absent',Y:'unknown'},positive:['A','C'],negative:[],history:[{source:'same',irrelevant:'red'}]}];
}
function direct(c){
 const stats={hypotheticalSuccessObjects:0,hypotheticalBitsets:0,candidateSpecsExamined:0,ruleChecks:0,proofNodes:0,rounds:0};
 const ledger=encode(c);
 if(c.positive.some(x=>c.negative.includes(x)))return {status:'conflict',yes:[],no:[],reasons:{},stats,ledger};
 const yes=new Set(c.positive),no=new Set(c.negative),reasons={};
 for(const x of c.positive){reasons['+'+x]=[['witness:'+x]];stats.proofNodes++;}
 for(const x of c.negative){reasons['-'+x]=[['negative_witness:'+x]];stats.proofNodes++;}
 let changed=true;
 while(changed){
  changed=false;stats.rounds++;
  if(stats.rounds>IDS.length+2)throw Error('unexpected cycle');
  for(const j of G.joins){
   stats.candidateSpecsExamined++;const why=[];
   for(const n of j.needs){stats.ruleChecks++;if(c.facts[n]==='absent')why.push(['absent:'+n]);}
   for(const id of yes){
    if(id===j.id)continue;stats.ruleChecks++;
    const p=j.ports.find(p=>JOIN[id].ports.includes(p));
    if(p)why.push(['realized:'+id,'shared_port:'+p]);
   }
   if(why.length){
    if(yes.has(j.id))return {status:'inconsistent',yes:[],no:[],reasons,stats,ledger};
    if(!no.has(j.id)){no.add(j.id);changed=true;}
    reasons['-'+j.id]=why;stats.proofNodes+=why.length;
   }
  }
  // Negative conclusion + all but one positive antecedent excludes the last one.
  for(const rule of G.implications){
   stats.ruleChecks++;if(!no.has(rule.then))continue;
   const missing=rule.when.filter(x=>!yes.has(x));
   if(missing.length===1){
    const x=missing[0];
    if(!no.has(x)){
     no.add(x);changed=true;
     reasons['-'+x]=[['not:'+rule.then,...rule.when.filter(y=>y!==x).map(y=>'realized:'+y),'law:contrapositive']];
     stats.proofNodes++;
    }
   }
  }
  for(const rule of G.implications){
   stats.ruleChecks++;
   if(rule.when.every(x=>yes.has(x))){
    if(no.has(rule.then))return {status:'inconsistent',yes:[],no:[],reasons,stats,ledger};
    if(!yes.has(rule.then)){
     yes.add(rule.then);changed=true;
     reasons['+'+rule.then]=[rule.when.map(x=>'realized:'+x).concat('joint_rule:'+rule.then)];
     stats.proofNodes++;
    }
   }
  }
 }
 return {status:'ok',yes:[...yes].sort(),no:[...no].sort(),reasons,stats,ledger};
}
function oracle(c){
 const stats={enumeratedCandidateSubsets:0,hypotheticalSuccessObjects:0,hypotheticalBitsets:0,portChecks:0,ruleChecks:0,acceptedModels:0};
 if(c.positive.some(x=>c.negative.includes(x)))return {status:'conflict',yes:[],no:[],stats,models:[]};
 const models=[];
 for(let mask=0;mask<(1<<IDS.length);mask++){
  stats.enumeratedCandidateSubsets++;stats.hypotheticalBitsets++;
  const realized=[];
  for(let bit=0;bit<IDS.length;bit++)if(mask&(1<<bit)){
   const j=G.joins[bit];realized.push({joinId:j.id,participants:[...j.ports],hypothetical:true});
   stats.hypotheticalSuccessObjects++;
  }
  const selected=new Set(realized.map(x=>x.joinId));
  if(c.positive.some(x=>!selected.has(x))||c.negative.some(x=>selected.has(x)))continue;
  if(realized.some(x=>JOIN[x.joinId].needs.some(n=>c.facts[n]==='absent')))continue;
  const ports=[];
  for(const x of realized)for(const p of x.participants){stats.portChecks++;ports.push(p);}
  if(new Set(ports).size!==ports.length)continue;
  let valid=true;
  for(const rule of G.implications){
   stats.ruleChecks++;if(rule.when.every(x=>selected.has(x))&&!selected.has(rule.then)){valid=false;break;}
  }
  if(!valid)continue;models.push(mask);stats.acceptedModels++;
 }
 if(!models.length)return {status:'inconsistent',yes:[],no:[],stats,models};
 return {status:'ok',yes:IDS.filter((_,i)=>models.every(m=>m&(1<<i))),
 no:IDS.filter((_,i)=>models.every(m=>!(m&(1<<i)))),stats,models};
}
function roundTrip(original,d){
 const packet=encode({version:'CRPP16-wire-v1',ledgerBase64:d.ledger.toString('base64'),
 consequence:{status:d.status,yes:d.yes,no:d.no,reasons:d.reasons}});
 const zipped=zlib.deflateRawSync(packet,{level:6});
 const unpacked=JSON.parse(zlib.inflateRawSync(zipped).toString('utf8'));
 const recovered=Buffer.from(unpacked.ledgerBase64,'base64');
 assert.equal(sha(recovered),sha(original));
 assert.equal(Buffer.compare(recovered,original),0);
 assert.deepEqual(unpacked.consequence.yes,d.yes);
 assert.deepEqual(unpacked.consequence.no,d.no);
 return {rawBytes:packet.length,compressedBytes:zipped.length,sha256:sha(recovered)};
}
function main(){
 const all=cases();
 const summary={cases:all.length,statusCounts:{},unsound:0,incomplete:0,roundTripFailures:0,
 direct:{hypotheticalSuccessObjects:0,hypotheticalBitsets:0,candidateSpecsExamined:0,ruleChecks:0,proofNodes:0,rounds:0},
 oracle:{enumeratedCandidateSubsets:0,hypotheticalSuccessObjects:0,hypotheticalBitsets:0,portChecks:0,ruleChecks:0,acceptedModels:0},
 packet:{rawBytes:0,compressedBytes:0,oracleRawBytes:0,oracleCompressedBytes:0,ledgerOnlyCompressedBytes:0},
 timingMs:{direct:0,oracle:0,serializeRoundTrip:0},
 heap:{start:process.memoryUsage().heapUsed,peak:0,end:0},examples:[],missingEntailments:[]};
 const ledgers={};
 for(const c of all){
  const original=encode(c);
  let t=performance.now(),d=direct(c);summary.timingMs.direct+=performance.now()-t;
  t=performance.now();const o=oracle(c);summary.timingMs.oracle+=performance.now()-t;
  t=performance.now();const packet=roundTrip(original,d);summary.timingMs.serializeRoundTrip+=performance.now()-t;
  assert.equal(d.status,o.status,'status mismatch '+c.caseId);
  if(d.status==='ok'){
   if(d.yes.some(x=>!o.yes.includes(x))||d.no.some(x=>!o.no.includes(x)))summary.unsound++;
   if(o.yes.some(x=>!d.yes.includes(x))||o.no.some(x=>!d.no.includes(x))){
    summary.incomplete++;summary.missingEntailments.push({caseId:c.caseId,directYes:d.yes,directNo:d.no,oracleYes:o.yes,oracleNo:o.no});
   }
  }
  for(const [k,v] of Object.entries(d.stats))summary.direct[k]+=v;
  for(const [k,v] of Object.entries(o.stats))summary.oracle[k]+=v;
  summary.packet.rawBytes+=packet.rawBytes;
  summary.packet.ledgerOnlyCompressedBytes+=zlib.deflateRawSync(original,{level:6}).length;
  summary.packet.compressedBytes+=packet.compressedBytes;
  const oracleWire=encode({version:'oracle-full-models-v1',ledgerBase64:original.toString('base64'),status:o.status,modelMasks:o.models});
  summary.packet.oracleRawBytes+=oracleWire.length;
  summary.packet.oracleCompressedBytes+=zlib.deflateRawSync(oracleWire,{level:6}).length;
  summary.statusCounts[d.status]=(summary.statusCounts[d.status]||0)+1;
  summary.heap.peak=Math.max(summary.heap.peak,process.memoryUsage().heapUsed);
  if(['alt-proofs','ledger-blue','ledger-red'].includes(c.caseId)){
   summary.examples.push({id:c.caseId,yes:d.yes,no:d.no,reasons:d.reasons,sha256:packet.sha256,models:o.models.length});
   ledgers[c.caseId]=packet.sha256;
  }
 }
 assert.equal(summary.unsound,0,'unsound deductions');
 assert.notEqual(ledgers['ledger-blue'],ledgers['ledger-red'],'ledger collision');
 assert((summary.examples.find(x=>x.id==='alt-proofs').reasons['-B']||[]).length>=2,'alternative proof missing');
 summary.heap.end=process.memoryUsage().heapUsed;
 summary.metadata={node:process.version,platform:process.platform,arch:process.arch,grammarJoins:IDS.length,
 grammarJointRules:G.implications.length,note:'Heap peak is process-wide sampled usage; timings are one uncalibrated run.'};
 console.log(JSON.stringify(summary,null,2));
}
if(require.main===module)main();
module.exports={makeCase,cases,direct,oracle};
