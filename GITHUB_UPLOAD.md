# Publish this project to GitHub

This archive is intentionally shipped without a `.git` directory.

```bash
git init
git add .
git commit -m "feat: initial RedTag production release"
git branch -M main
git remote add origin git@github.com:YOUR_ORG/redtag.git
git push -u origin main
```

Before pushing, verify `.env` is not staged and run the CI checks locally.
