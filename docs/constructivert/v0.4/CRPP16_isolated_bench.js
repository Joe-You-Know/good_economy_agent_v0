'use strict';
// Run: node --expose-gc docs/constructivert/v0.4/CRPP16_isolated_bench.js direct
// And separately with oracle; repeat in clean processes.
const {cases,direct,oracle}=require('./CRPP16_broader_verifier');
const {performance}=require('node:perf_hooks');
const mode=process.argv[2]||'direct';
if(!['direct','oracle'].includes(mode))throw Error('Use direct or oracle');
const fn=mode==='direct'?direct:oracle;
const inputs=cases();
if(global.gc)global.gc();
const baseline=process.memoryUsage();
let peak=baseline.heapUsed,checksum=0;
const start=performance.now();
for(const c of inputs){
 const r=fn(c);
 checksum+=(r.yes?.length||0)+(r.no?.length||0)+(r.stats?.hypotheticalSuccessObjects||0);
 peak=Math.max(peak,process.memoryUsage().heapUsed);
}
console.log(JSON.stringify({mode,cases:inputs.length,elapsedMs:performance.now()-start,
 initialHeapUsed:baseline.heapUsed,peakHeapUsed:peak,heapDeltaPeak:peak-baseline.heapUsed,
 maxRSSKiB:process.resourceUsage().maxRSS,checksum}));
