# Fresh user CPU run plan

```mermaid
flowchart TD
    A[Published HTTPS repository and pinned SHA] --> B[AUTO-user-run.py bootstrap]
    B --> C{Anonymous remote and SHA available?}
    C -- no --> F[Stop with visible source failure]
    C -- yes --> D[Create fresh ~/runs root: repo, data, configs]
    D --> E[Clone pinned SHA; assert clean tree and origin]
    E --> G{Identity correct?}
    G -- no --> F
    G -- yes --> H[Atomically generate configs/.runrc mode 0600]
    H --> I[Start named tmuxinator user session]
    I --> J[AUTO-user-run.py execute checks runrc]
    J --> K{Contract complete?}
    K -- no --> F
    K -- yes --> M[Generate public synthetic input in data]
    M --> N[Build five wheels from cloned source into data/wheels]
    N --> O{Build and install succeed?}
    O -- no --> L
    O -- yes --> P[Run three CLI stages and composed CLI]
    P --> Q{Outputs match expected schema and each other?}
    Q -- no --> L
    Q -- yes --> R[PASS receipt and hashes in data/evidence]
    R --> S[Structured tester verdict and dated runbook]
```

The first public clone is the acceptance boundary. A local clone or copied model/data
cannot establish a pass. The synthetic CPU providers exercise packaging and file
contracts; they do not establish genuine generation, correction, or ERRANT quality.

## Command contract

| Program | Input | Output and side effects | Failure |
|---|---|---|---|
| `AUTO-user-run.py bootstrap` | HTTPS URL, full SHA, optional absolute base | Creates a new three-directory run root and the named tmuxinator user session; prints base, SHA and switch command | Refuses existing root, inaccessible source, wrong SHA, dirty clone |
| `AUTO-user-run.py execute` | `--base` absolute run root | Writes only under `data/` and reads generated `configs/.runrc`; prints progress and writes evidence | Stops at first failed gate; writes FAIL receipt |

The bootstrap owns all `.runrc` fields. It derives the SHA from the clone and
the paths from the fresh base, and replaces the file atomically. No manual field
entry or credential lookup is part of this CPU experiment.
