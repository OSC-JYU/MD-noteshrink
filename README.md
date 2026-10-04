# MD-noteshrink

[noteshrink](https://github.com/mzucker/noteshrink) for MessyDesk: cleans up scans of notes and
documents by reducing them to a few colours. The user help is [help/index.md](help/index.md)
(served at `/help`); the task and its settings are in [service.json](service.json) (served at
`/config`).

| Task | Input | Output |
|---|---|---|
| `clean` | PNG or JPEG image | `<image label>.png`, type `image` (an indexed PNG) |

Params: `num_colors` (2–64, default 8), `value_threshold` and `sat_threshold` (percent, defaults
25 and 20), `sample_fraction` (percent of pixels sampled for the palette, default 5), `white_bg`
and `saturate` (booleans, defaults false and true).

`noteshrink.py` is the original script (with its PDF step turned off); `api.py` calls its
functions for one image.

## Running

```bash
make build
make start
```

The service listens on port 9023. `make` uses podman; `CONTAINER_RUNTIME=docker make build` for
Docker.

### Example call (HTTP mode)

	curl -F "message=@test/clean.json;type=application/json" -F "content=@test/notesA1.jpg" \
	  http://localhost:9023/process

## Storage modes

- **Disk mode** when `MD_PATH` points at the MessyDesk root (the directory that contains `data/`):
  the image is read from `message.file.path`, the result is written to `MD_PATH/data/<db>/tmp/`,
  and `/config` reports the `elg_fs` adapter.
- **HTTP mode** otherwise, or with `STORAGE_MODE=http`: the image is the `content` upload, the
  result is served once from `/files/<name>.png`, and `/config` reports `elg`.

`/config` serves service.json with the adapter of the mode; `SERVICE_ID`, `SERVICE_NAME`,
`SERVICE_ADAPTER` and `SERVICE_LOCAL_URL` override its fields (`md_service.py`).

## Tests

```bash
make test
```

Runs `tests/test_api.py` in the service image: the task in both modes, the settings, and
`/config`, `/help` and `/health`.
