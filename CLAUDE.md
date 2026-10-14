# tufteseid-render — the server-side render sidecar

Python 3.11, stdlib HTTP, no framework. Takes a PocketBase evidence row, renders
Norwegian LiDAR terrain with RVT-py and ffmpeg, and PATCHes the file back with
the caller's own token. Two producers: `sunloop` and `rvt`.

Split out of [tufteseid](https://github.com/buzh/tufteseid) in October 2026,
where it lived as `rendersvc/`. That repo is the only caller and the other half
of every contract here.

## Docs

`docs/render-sidecar.md` owns the subject — the HTTP contract, the token trade,
the queue's limits, the ground, the RVT and ffmpeg recipes, the burnt-in legend,
the failure modes, adding a producer. `README.md` is the third-party install and
admin guide. Read the first before touching any `.py`.

## The two-repo seams

Four things are stated in both repos and must agree. Changing one here is a pull
request there as well:

| Seam | Here | There |
| --- | --- | --- |
| The `render` feature string | `server.py`'s `admit` | `src/auth/features.ts` |
| The `meta.job` protocol and `BEAT_S` | `Heartbeat`, the worker's marker writes | `src/evidence/queue.ts`, which condemns a marker after five beats |
| The legend's field names and `{res}`/`{credit}` tokens | `legend.py`, `server.py`'s `legend_of` | `src/evidence/legendContent.ts` |
| A row's `kind` and its stored `meta` | each producer's `spec_of` | `src/evidence/spec.ts`, plus the migration that adds the kind to `evi_kind` |

`tiff.py` is a **deliberate second copy** of the float-TIFF reader in
tufteseid's `vat-cache/fetch_dem.py`. The split cut the import, not the
coupling: one endpoint, one set of quirks, and a fix learned at either end is
carried to the other by hand.

## Working here

- **No local build.** The workstation has no docker daemon. Print the commands
  for the user to run on the server, or let the `build` workflow run them on a
  pull request.
- **A module named `rvt.py` would shadow the installed `rvt` package**, which is
  why the blends live in `blends.py`.
- **rvt-py is pinned to 2.2.3 and installed `--no-deps`**, and `scipy<1.15` and
  `matplotlib<3.10` are caps that 2.2.3 needs rather than anything this code
  wants. All three are *startup* failures: `server.py` imports the producers, so
  a wrong version answers no route at all. The `build` workflow imports `server`
  against the finished image for exactly that reason.
- **The base image must stay under Python 3.12.** rvt-py 2.2.3 declares
  `<3.12`, and pip reports that as a version that does not exist rather than as
  a conflict.
- **Verify an upstream pin before shipping it** — that the tag exists and that
  the version has the feature. Guessing one is how a deploy fails.
- **No comments.** The code is the documentation. No module headers beyond the
  docstring, no quirk notes, no provenance for a magic number, no `docs/*.md`
  pointers in source. Everything the code cannot carry goes in
  `docs/render-sidecar.md`, and a name or a named constant carries the rest.

  Module and function **docstrings stay** — they are strings rather than
  comments and the only narrative left in the source. So does a load-bearing
  directive, which is machine-read and not prose: `# noqa`, a shebang, a licence
  banner. Those stay bare, with no reason appended.
- **Docs state the present tense.** A change that reverses an earlier decision
  rewrites the paragraph that stated it rather than appending a correction. The
  record of the reversal is the commit.
- **Commits**: short imperative subject; body explains the *why* when the diff
  doesn't. Write the `Co-Authored-By` trailer yourself — nothing adds it.

## Publishing

A push to `main` publishes `ghcr.io/buzh/tufteseid-render:main` and a
`sha-<commit>` tag; a `v*` git tag publishes the version, the major.minor, and
`latest`. Consumers pin a version tag, so **a render change is live only once
tufteseid's `docker-compose.yml` is bumped to it** — the deploy is two commits
in two repos, and that is the trade the split bought.
