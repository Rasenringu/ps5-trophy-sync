# Prepare a Git repository

The source tree includes the current application, pinned build/dependency inputs,
meaningful tests, contracts and concise documentation. Builds, reports, captures,
credentials and databases are ignored. The cleanup task did not configure a remote, create a commit or push anything.

From the repository root, inspect the exact files Git would include:

```powershell
git status --short
git ls-files --cached --others --exclude-standard
git check-ignore config/local.json .local/app.env artifacts/console/final-ui/TrophySync.elf
```

Keep `.gitignore`, all dependency locks, vendor font/license notices and
`console/COPYING`. Never force-add `.local`, captures, TLS keys, credentials,
personal databases or generated binaries. Publisher artwork is stored privately
in the application's database, not in this source tree.

Historical generated directories in an existing workspace can be reviewed with:

```powershell
.\scripts\Clean-GeneratedFiles.ps1 -WhatIf
# Remove only those reviewed historical paths:
.\scripts\Clean-GeneratedFiles.ps1
```

The script validates paths/reparse points, skips the historical Linux-linked
dependency cache rather than following links, and preserves the current final build,
current dependency cache, TLS, SDK archive, local configuration and real database
backup. A fresh clone has none of these historical generated directories.
During automated cleanup, shell deletion was blocked by execution policy; the
script is provided for a manual local run. Those remaining paths are ignored and
are not required to build the current application.

After reviewing the files, choose a repository license for your own web/API code,
set your Git identity and create your local commit. Console code's GPL requirements
and third-party notices remain applicable; see [THIRD_PARTY](THIRD_PARTY.md).
Add the remote you choose and push through your normal Git authentication when
ready. Do not embed access tokens in a remote URL. Binary publication is separate
and needs the corresponding source/build inputs described in the license notes.
