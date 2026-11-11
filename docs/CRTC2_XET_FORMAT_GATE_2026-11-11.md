# CRTC2 on the exact Hugging Face Xet reference CSV — format-gate result

**Date:** 2026-11-11  
**Decision:** `UNSUPPORTED_FORMAT`; no constructive payload created; no buyer selection or sale.

## Implementation provenance

The original `constructive_codec_adaptive_v0_2_source_evidence.zip` was recovered from the owner's file library and its `constructive_codec_v0_2/crcodec/codec.py` inspected and exercised locally. The package README explicitly says the adaptive selector keeps the **CRTC1** constructive payload format unchanged. This implementation accepts only complete, correctly ordered PCL v0.3 clockwise shell TSV records; it is **not** an arbitrary-file codec.

`crcodec.codec.encode` calls `_source_scan`. At shell 1, it requires the *first line* to start with `b"1\\t0\\tV\\tUP\\t"` or `b"1\\t0\\tV\\tDOWN\\t"`. Otherwise it raises `CodecError("bad shell 1 start or absent seam")`. This is a mandatory format condition, not an optimization fallback.

## Official source prefix verified remotely

The official source is `Electric_Vehicle_Population_Data_20250917.csv` in `xet-team/xet-spec-reference-files`. Remote Hugging Face CPU-basic probe: https://huggingface.co/jobs/joe-you-know/6af491a8ab34849891ae3ea1

It downloaded the start of that specific file and printed the first 512 bytes. The first line begins:

```text
VIN (1-10),County,City,State,Postal Code,Model Year,Make,Model,Electric Vehicle Type,...
```

That prefix cannot satisfy the CRTC1 shell 1 seam. The precise source SHA-256 from the previously completed, byte-exact Xet verification is `f41255b252f776125f2b657136654e4d4d5d2ccf8ef4db0ec186bd1981b69734` (63,527,244 bytes).

The recovered original encoder was invoked locally with the official header. It raised:

```text
CodecError: bad shell 1 start or absent seam
```

No `.crtc` file was created. The codec is known to terminate at this first-line check; transferring all 63.5 MB to the local runner would not change this deterministic rejection. **A full-file encoder invocation was not performed.** The local codec's existing Python pytest suite passed **19/19 tests**, confirming that its intended supported format remains functional; that does not establish a general-purpose format.

## What this is *not*

This is not a measured CRTC2 compression ratio on the Xet CSV. It is not a CRTC2 decoding failure after encoding, and is not evidence against its measured advantage for the previously tested shell records. Do not reclassify the original CSV under an invented shell grammar, replace CRTC2 with a generic zlib wrapper, or reuse the 95 KB source-history benchmark as an encoded size for this 63.5 MB CSV.

The preexisting buyer policy and $4.99 perpetual / opt-in $0.99 monthly updates offer are **unchanged**. The buyer result for the Xet dataset remains `NO_DECISION_INCOMPLETE_EVIDENCE`, with `unsupported_source_format` as the recorded reason.

## Engineering requirement for an admissible future test

Define and implement a separately versioned, lossless general-data constructive representation for arbitrary byte streams, or a fully specified CSV grammar, with explicit evidence of which distinctions are regenerated and which remain encoded. Independently SHA-256-verify round trips, include adversarial arbitrary files, report encoded size and compute cost, then compare on the same original Xet source under matched conditions. That would be **a new codec capability** and must not be misrepresented as a property of today's CRTC1 payload.
