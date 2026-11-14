# Windows Git delivery

The delivered package includes this script, `research-revision.bundle`, and
`delivery-manifest.json`. Keep them in the same extracted folder. The bundle
contains the complete committed revision branch and its reachable history.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Publish-Revision.ps1
```

Git must be installed and an authorized GitHub credential helper/session must
already work for this repository. Git author configuration does not authenticate
to GitHub. Never paste credentials into the script or command.

The script verifies the bundle hash and branch tip, uses a new isolated checkout,
checks the expected GitHub remote, configures the requested author identity, and
pushes only `research/publication-ready-revision`. It never force-pushes or updates
the default branch. Existing checkouts and their uncommitted work are untouched.
A divergent remote research branch causes a nonzero exit without a push; a
concurrent non-fast-forward update is also rejected by ordinary Git push rules.

For an offline import check without contacting GitHub:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Publish-Revision.ps1 -VerifyOnly
```

This clones and checks the local bundle. It does not test GitHub authentication
or guarantee that a future push will be permitted. A successful real push prints
the branch and commit URLs. No journal submission is performed.

The final assessment of the research draft is 7.9/10 in a sequential automated
review, below the requested 9/10 threshold. It is not an external peer review or
a publication-readiness guarantee. See the committed review and evidence records.
