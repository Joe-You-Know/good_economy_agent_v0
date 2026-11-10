# ConstructiveRT Native v0.23 — source and verification checkpoint

**Recorded:** 2026-11-10. **Scope:** evidence for the separate ConstructiveRT research project. This is a documentation checkpoint in Good Economy Agent; it is **not a claim that the v0.23 source tree has been committed here**. The older v0.22 native source snapshot remains isolated in draft PR #4 and should not be merged as if it were the v0.23 release.

## Native v0.23 capability

- C++20 + CMake, Windows MSVC, libcurl, OpenSSL SHA-256, SQLite.
- Native HTTP(S) full GET and ranged transfers.
- Independent SHA-256 verification, atomic content-addressed cache publication, source- and ETag-bound resumable chunks, native file locking, and observation ledger.
- Opt-in `--timings` phase measurements; these are overlapping observations, not a sum-to-wall-time decomposition.
- The source's original 27-entry release manifest was checked against the supplied v0.23 files: **27/27 correct SHA-256 and sizes**.

## Windows x64 evidence (user-operated)

The supplied `windows-test-results/result.json` reports Visual Studio 17 2022, CMake 4.4.4, successful configure/build, and three passing CTest suites:

1. `native_foundation`
2. `native_cli_adversarial`
3. `native_http_adversarial`

The recorded executable digest is `755f1d692012cd11017269abcc1bde22ecbe683b971925269ce1278792a2564d`. These are inspected run records, not a Windows test rerun from the GitHub connector.

## Balanced real-WAN Windows benchmark

From the supplied `benchmark-windows-v023/summary.json`, generated 2026-11-10T16:28:44Z:

| Method | Median elapsed |
| --- | ---: |
| curl + independent hash | 1943.249 ms |
| Native full GET | 1988.228 ms |
| Native 4-worker ranges | 1999.053 ms |

- Twelve trials for each method (36/36 completed and independently hash-verified).
- All six possible ordering permutations were rotated twice.
- Official NumPy 2.1.3 `cp312-win_amd64` wheel; 12,566,858 bytes.
- Trusted wheel SHA-256: `0d30c543f02e84e92c4b1f415b7c6b5326cbe45ee7882b6b77db7195fb971e3a`.
- Native full GET was **about 2.3% slower** than curl by the recorded medians; native ranges **about 2.9% slower**.
- No general speed improvement is established; comparisons depend on hardware, path, server, and test window.

## Separate controlled localhost test

The supplied Linux 12-round loopback record shows 36 verified transfers: curl 18.361 ms, native full GET 44.660 ms, native ranges 92.977 ms (medians). This is not a WAN speed comparison.

## Independent Linux rerun of curated source (2026-11-10)

A clean CMake Release build was completed in an isolated Linux work directory. CTest reported **3/3 suites passed**, including native foundation, CLI adversarial, and HTTP adversarial suites. This is a fresh test of the curated v0.23 source, not an independent security audit or end-to-end reproduction of the user's Windows WAN network.

## Provenance and migration boundary

- Original uploaded whole-project archive SHA-256: `14ba998b296d9fbdeea33955cd3b0ebde0a8717fcd18de6d20ebacccf8cc0039`.
- Separately prepared standalone GitHub-ready ZIP SHA-256: `34157385aaf87f863c7b53cf1aae1222be135642c3cd4574c2db7d3ccaeca7a7`. The latter contains 137 curated source and documentation files, with build products, generated downloads, personal logs, and third-party static libs removed.
- The GitHub-ready source archive remains a **local conversation artifact** at the time of this checkpoint and **has not been uploaded to this repository**. Do not treat this document as the source itself.
- The source did not include a repository-wide open-source license; choose licensing explicitly before inviting external reuse.
- The intended dedicated destination is `Joe-You-Know/ConstructiveRT`, when repository creation and source push are available.

## Next work

1. Create the independent ConstructiveRT repository and import the curated source tree as individual text files.
2. Verify uploaded source hashes and run Windows/Linux tests against its actual Git checkout.
3. Keep CI initially opt-in or disabled to avoid unexpected Actions usage.
4. Design crash-consistent checkpoint batching and test process interruption before optimizing range transfers.
5. Link the standalone repository from the GitHub Portfolio, distinguishing verification from current research claims.

The Good Economy Agent can reference this artifact as an owned-engineering asset without implying verified profitability, automatic commercial deployment, or production certification.
