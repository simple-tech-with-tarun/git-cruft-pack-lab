# Git Cruft Pack Lab

## Overview

This repository demonstrates how Git handles unreachable objects using **Cruft Packs**.

The lab explores what happens when a branch is deleted, its reflog entries are expired, and its commits become unreachable. It then demonstrates how Git stores these objects in cruft packs and eventually removes them through expiration and repacking.

## Learning Objectives

- Understand reachable and unreachable Git objects.
- Identify unreachable objects using `git fsck`.
- Understand how reflogs affect object reachability.
- Create and inspect Git cruft packs.
- Understand the purpose of `.pack`, `.idx`, `.mtimes`, and `.rev` files.
- Explore how Git expires and removes unreachable objects.

---

## 1. Creating Unreachable Objects

A feature branch was created from `main`:

```powershell
git switch -c feature/application-metadata
```

Additional application metadata was introduced through two commits:

```text
feat: add application owner metadata
feat: add application status metadata
```

The feature branch was then deleted:

```powershell
git switch main
git branch -D feature/application-metadata
```

Although the branch reference was removed, its commits initially remained accessible through the reflog.

## 2. Expiring Reflogs

Git reflogs maintain a record of previous reference positions, which can help recover commits after branch deletion.

To remove the reflog references in this isolated lab:

```powershell
git reflog expire --all --expire=now
```

Verify the reflog:

```powershell
git reflog --all --oneline
```

The reflog was empty after expiration.

## 3. Identifying Unreachable Objects

Run:

```powershell
git fsck --full --unreachable
```

Git identified six unreachable objects:

| Object type | Count |
|---|---:|
| Commits | 2 |
| Trees | 2 |
| Blobs | 2 |
| **Total** | **6** |

The objects were no longer referenced by branches or reflogs, but they still existed in Git's object database.

## 4. Creating a Cruft Pack

Git can retain unreachable objects in a separate cruft pack instead of immediately removing them.

Run:

```powershell
git gc --cruft --no-prune
```

The `--cruft` option creates a cruft pack for unreachable objects.

The `--no-prune` option prevents this garbage-collection operation from pruning unreachable objects.

This allows the objects to remain available for recovery.

## 5. Inspecting Pack Files

List the pack directory:

```powershell
Get-ChildItem .git\objects\pack
```

The experiment produced two packfiles:

- A regular pack containing reachable objects.
- A cruft pack containing unreachable objects.

A cruft pack is identified by its `.mtimes` companion file.

### Pack file components

| File | Purpose |
|---|---|
| `.pack` | Stores compressed Git objects. |
| `.idx` | Indexes objects inside the pack. |
| `.mtimes` | Stores object modification-time metadata used for cruft expiration. |
| `.rev` | Reverse index mapping pack positions to object IDs. |

### Verifying cruft pack contents

Use the `.idx` file with `git verify-pack`:

```powershell
git verify-pack -v .git/objects/pack/pack-<hash>.idx
```

The output displays object IDs, object types, sizes, offsets and delta information.

The two previously deleted commits were found inside the cruft pack.

Git could still read them:

```powershell
git cat-file -t 86070e6
git cat-file -t 5872425
```

Both returned:

```text
commit
```

This demonstrated that unreachable objects can remain accessible while stored in a cruft pack.

## 6. Testing Cruft Pack Expiration

Git uses the timestamps stored in the `.mtimes` file to determine whether unreachable objects have passed an expiration cutoff.

The default `gc.pruneExpire` setting is typically:

```text
2.weeks.ago
```

It was not explicitly configured in this repository.

### Experiment A: Two-week expiration

Run:

```powershell
git repack -d --cruft --cruft-expiration="2.weeks.ago"
```

This command:

- Reorganizes objects into packfiles.
- Creates a replacement cruft pack.
- Excludes objects whose recorded modification times are older than the expiration cutoff.
- Uses `-d` to remove redundant old packfiles after repacking.

Note: `-A` (`--all`) cannot be combined with `--cruft`.

The two commits remained accessible because their recorded modification times had not crossed the two-week cutoff.

Verification:

```powershell
git fsck --full --unreachable
```

The six unreachable objects were still reported.

### Experiment B: Immediate expiration

For a controlled expiration test, run:

```powershell
git repack -d --cruft --cruft-expiration=now
```

This uses the current time as the expiration cutoff.

The six unreachable objects became eligible for expiration and were excluded from the replacement cruft pack.

The `-d` option allowed the redundant old packfiles to be removed.

Verification:

```powershell
git fsck --full --unreachable
```

No unreachable objects were reported.

Check the previously deleted commits:

```powershell
git cat-file -t 86070e6
git cat-file -t 5872425
```

Both returned:

```text
fatal: Not a valid object name
```

This confirmed that the unreachable commits were no longer available in the local object database.

---

## 7. Key Takeaways

1. Deleting a branch does not immediately delete its commits.
2. Reflogs can retain references to commits after branch deletion.
3. Expiring reflogs can make commits unreachable.
4. Unreachable objects are not necessarily deleted immediately.
5. Cruft packs allow Git to retain unreachable objects separately.
6. The `.mtimes` file provides timestamp metadata used for expiration decisions.
7. `git verify-pack` can inspect and verify the contents of packfiles through their index files.
8. Expiration and repacking can remove unreachable objects from the object database.

## Conclusion

This lab demonstrated the lifecycle of unreachable Git objects, from branch deletion and reflog expiration to cruft pack creation and eventual object removal.

The central concept is:

**Unreachable does not mean deleted.**

Git can preserve unreachable objects in cruft packs for a retention period, allowing recovery before they become eligible for expiration and pruning.
