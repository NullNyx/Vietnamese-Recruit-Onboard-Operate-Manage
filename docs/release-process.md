# Release process

Các bước release một phiên bản just-harness mới.

## Checklist release

```bash
# 1. Ensure clean working tree
git status --short

# 2. Update CHANGELOG.md
#    Thêm entry [vX.Y.Z] với ngày, nhóm Added/Fixed/Changed.
vim CHANGELOG.md

# 3. Commit changelog
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for vX.Y.Z"

# 4. Tag + push
git tag -a vX.Y.Z -m "vX.Y.Z — <tóm tắt>"
git push origin main --follow-tags

# 5. Create GitHub release
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file CHANGELOG.md --latest

# 6. Verify CI xanh tại tag mới
gh run list --limit 1
```

## Lưu ý

- Version theo semver: vMAJOR.MINOR.PATCH (pre-release: v0.x.y).
- CHANGELOG giữ format Keep a Changelog: Added / Fixed / Changed / Removed.
- Tag phải trùng version trong CHANGELOG heading.
- `--follow-tags` đẩy cả commit và tag trong một push.
- Release note lấy từ CHANGELOG, không viết lại.

## Mẫu tóm tắt

| Version | Tóm tắt |
|---------|---------|
| v0.1.0 | Initial scaffold release. Core harness + docs + GitHub setup. |
| v0.1.1 | Bugfix: install-harness missing from copy list, archive dir missing. |
