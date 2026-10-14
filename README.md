# tufteseid-render

The server-side render sidecar for
[tufteseid](https://github.com/buzh/tufteseid). It turns a stored evidence row
into a picture of Norwegian LiDAR terrain and writes the file back onto the
record it came from.

Two renders are too slow to make in a browser tab:

- **a sun loop** — a 360° sun rotation over one rectangle, 72 hillshades of a
  single elevation grid encoded as a VP9 WebM, cited in its own pixels;
- **an RVT blend** — e4MSTP today, a stack of horizon scans over a grid with
  hundreds of metres of real ground around it, stored as an RGBA PNG.

Both are a minute or two of two cores. Everything else tufteseid keeps is
rendered in the reader's own tab.

Python 3.11, stdlib HTTP, no framework.
[RVT-py](https://github.com/EarthObservation/RVT_py) does the visualizations and
ffmpeg the encode. Elevation comes straight from
[hoydedata.no](https://hoydedata.no)'s ImageServer.

## What it is for

This is a sidecar, not a general render API. It is useful to you if you run
tufteseid; on its own it renders nothing, because a job names a PocketBase
record and reads its parameters and its rectangle from there.

It holds **no credentials**. Every call it makes to PocketBase carries the
requesting reader's own token, so a job can touch exactly what that reader can
and the permission model is not restated here.

## Running it

The image is published to `ghcr.io/buzh/tufteseid-render`. Pin a version tag;
tufteseid's `docker-compose.yml` already does:

```yaml
rendersvc:
  image: ghcr.io/buzh/tufteseid-render:0.1.0
  restart: unless-stopped
  cpus: 2.0
  mem_limit: 2g
  environment:
    - POCKETBASE_URL=http://pocketbase:8090
    - PUBLIC_ORIGIN=https://example.org
```

and a reverse proxy puts it under `/render/*` on the same origin as the app.

| Variable | What |
| --- | --- |
| `POCKETBASE_URL` | where the records are. Defaults to `http://pocketbase:8090` |
| `PUBLIC_ORIGIN` | the address **your** readers visit |

`PUBLIC_ORIGIN` has no sensible default and is worth getting right. A sun loop
is cited in its own pixels, and the short link burnt into that band is composed
from the stored record and this origin rather than taken from the request, so
that nobody can forge one. Left unset, a loop is rendered with no link in its
band. Both variables are read at startup, so changing either recreates the
container.

`GET /render/health` answers `{ok, pending, capacity}`, where `ok` is the worker
thread's liveness — 200 while it runs, 503 once it is gone. A queue depth is not
health, so that is the one thing a probe has to look at.

### Building it yourself

```sh
docker build -t tufteseid-render .
```

The build context is the repo root and there is nothing to configure. The base
image must stay under Python 3.12 — rvt-py 2.2.3 declares `<3.12`, and pip
reports that not as a conflict but as a version that does not exist.

## What it costs you

Capped for you, and none of the caps can be raised from a request:

- signed-in readers only, and only those whose account carries the `render`
  feature;
- one job at a time per reader, a queue of eight behind one serial worker;
- `cpus: 2.0` and `mem_limit: 2g` on the container;
- the rectangle, the resolution and the frame count come from the stored
  record, never from the request body.

The worst case the rectangle cap allows measures 315 s and 1.0 GB of RSS. Jobs
fetch elevation directly from hoydedata.no rather than through any cache,
because every job is a rectangle nobody will ask for again.

## Docs

[`docs/render-sidecar.md`](docs/render-sidecar.md) is the whole subject: the
HTTP contract, the token trade, the queue's limits, how the ground is fetched
and where a row is settled empty, the RVT and ffmpeg recipes, the burnt-in
legend, the failure modes, and what adding a producer takes. The caller's half
of the same contract is tufteseid's `docs/render-sidecar.md`.

## Licence

MIT. See [`LICENCE`](LICENCE).
