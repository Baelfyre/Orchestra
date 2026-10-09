# Signed Commit Readiness

## Purpose

Record the current signed-commit readiness state for the solo maintainer and define the active signed-commit workflow without changing repository rulesets, rewriting history, or weakening recovery options.

## Current Repository Policy

- The active `Protect main` ruleset already includes `required_signatures`.
- Maintainer bypass remains enabled for solo-maintainer recovery.
- Signed-commit readiness is complete for the current local repository workflow.

## Readiness Outcome

`SIGNED_COMMIT_READY`

Current evidence:

- `commit.gpgsign` is configured locally as `true`.
- `gpg.format` is configured locally as `ssh`.
- `user.signingkey` is configured locally to the dedicated public signing key file `orchestra_signing_ed25519.pub`.
- `gpg.ssh.allowedSignersFile` is configured locally as `.git\allowed_signers`.
- local `gpg` is not installed.
- OpenSSH is installed locally.
- a dedicated SSH signing key now exists locally for this repository workflow.
- no GitHub GPG signing key was needed.
- a GitHub SSH signing key is registered for the maintainer account.
- signed test branch: `test/signed-commit-check`
- signed test commit: `e43202e21755b9e9e1dd6de511fa4452a93fe27d`
- local verification showed `Good "git" signature` and `%G?` status `G`
- GitHub verification for the test branch commit returned `verified: true` and `reason: "valid"`
- `main` history was not rewritten and the verified test stayed isolated on a test branch.

## Recommended Signing Method

Recommended method: `SSH`

Reason:

- Windows already has OpenSSH available.
- local Git version supports modern signing workflows.
- GPG is not installed, so GPG signing would add more tooling work than needed.
- S/MIME is unnecessary for this repository.

This recommendation is now implemented locally for this repository.

## Completed Setup

1. A dedicated ED25519 SSH signing key was created for commit signing.
2. The public key was added to GitHub as an SSH signing key.
3. Local Git was configured for repo-local SSH signing.
4. A signed test commit was created on a non-`main` test branch.
5. The commit was verified locally and on GitHub before any `main` history change.

Do not:

- create or store private keys in the repository
- print private key material into logs or docs
- rewrite or amend old repository history for readiness work
- use bypass for routine unsigned development
- merge the signing test branch into `main` without explicit approval

## Normal Signed-Commit Workflow

1. Create a branch.
2. Make changes.
3. Run local validation.
4. Commit with signing enabled.
5. Push the branch.
6. Open a pull request.
7. Wait for required checks.
8. Merge only after checks pass.

## Emergency Bypass Workflow

Maintainer bypass remains available only for:

- ruleset repair
- CI repair
- repository access recovery
- urgent governance correction

If bypass is used and it affects governance behavior, CI behavior, release state, or repository protection state, document it afterward in the implementation report or `CHANGELOG.md`.

## Verification Commands

Local verification:

```powershell
git log --show-signature -n 5
git log --format="%h %G? %GS %s" -n 10
git config --show-origin --get commit.gpgsign
git config --show-origin --get gpg.format
git config --show-origin --get user.signingkey
```

GitHub verification:

```powershell
gh api repos/Baelfyre/Orchestra/commits/main --jq ".commit.verification"
```

Expected healthy direction:

- new signed commits should show `G` locally
- GitHub should report `verified: true` for newly signed commits

## Optional Local Configuration Examples

These examples match the current repo-local SSH signing setup. Keep them local to the repository unless broader maintainer rollout is explicitly approved.

```powershell
git config --local commit.gpgsign true
git config --local gpg.format ssh
git config --local user.signingkey "$env:USERPROFILE\.ssh\orchestra_signing_ed25519.pub"
```
