# Tools

Standalone helper scripts for probing the SocialHackAPI lab from the
outside - not part of the Flask app itself (`app/`). You run these against
a running instance of the lab the same way you'd use curl or Postman.

## endpoint_checker.py

Logs in, then probes a list of API endpoints with GET/POST/PUT/PATCH/DELETE/
OPTIONS and reports every `(endpoint, method)` combination the server
accepts - anything other than a plain 404/405. Useful for spotting an
endpoint that quietly accepts a method you didn't expect (e.g. a GET-only
endpoint that also accepts DELETE).

The endpoint list lives in `endpoints.txt` next to the script, and the
target address is a `--url` flag instead of being hardcoded - so if the
lab's host/port ever changes, updating one flag (or one line in
`endpoints.txt`) is all it takes.

> **Heads up:** this really sends every method, including PUT/DELETE, with
> a real request body. Against endpoints like `/users/1` that have no
> ownership check (by design, in this lab), a DELETE can genuinely delete
> that record. Re-seed the database (`python run.py --reset`) if a scan
> leaves data - including the account you logged in with - in a weird
> state.

### Usage

```bash
pip install requests

# uses the defaults (http://localhost:5001/api/v1, alice/password123)
python3 endpoint_checker.py

# point at a different address
python3 endpoint_checker.py --url http://localhost:5001/api/v1

# point at a different address with different credentials
python3 endpoint_checker.py --url http://192.168.1.50:5001/api/v1 --username bob --password password123

# use a different endpoint list
python3 endpoint_checker.py --endpoints my-endpoints.txt
```

| Flag | Default | Meaning |
|---|---|---|
| `--url` | `http://localhost:5001/api/v1` | Base API URL |
| `--endpoints` | `endpoints.txt` (this folder) | Path to the endpoint list |
| `--username` | `alice` | Login username |
| `--password` | `password123` | Login password |
