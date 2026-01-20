# GitHub Setup Guide for Insurance Project

## Current Status
- Git repository is initialized
- Current remote: `https://github.com/batbayarr/silicon4.git`
- Branch: `main` (behind origin/main by 3 commits)
- Many insurance-related changes ready to commit

## Option 1: Create New Repository and Change Remote

### Steps:
1. Create a new repository on GitHub (e.g., `silicon4_insurance`)

2. Change the remote URL:
   ```bash
   git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO.git
   ```

3. Verify the remote:
   ```bash
   git remote -v
   ```

4. Stage all changes:
   ```bash
   git add .
   ```

5. Commit the changes:
   ```bash
   git commit -m "Initial commit: Insurance module implementation"
   ```

6. Push to the new repository:
   ```bash
   git push -u origin main
   ```

## Option 2: Keep Same Repository, Use Different Branch

### Steps:
1. Create a new branch for insurance:
   ```bash
   git checkout -b insurance-module
   ```

2. Stage and commit changes:
   ```bash
   git add .
   git commit -m "Insurance module: Add models, views, templates, and API endpoints"
   ```

3. Push the new branch:
   ```bash
   git push -u origin insurance-module
   ```

## Option 3: Start Fresh (New Repository)

### Steps:
1. Remove current remote:
   ```bash
   git remote remove origin
   ```

2. Create new repository on GitHub

3. Add new remote:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO.git
   ```

4. Push to new repository:
   ```bash
   git push -u origin main
   ```

## Files Ready to Commit

### Modified Files:
- config/urls.py
- core/admin.py
- core/db_router.py
- core/middleware.py
- core/models.py
- core/thread_local.py
- core/urls.py
- core/views.py
- databases.txt
- requirements.txt
- templates/base.html

### New Files/Directories:
- core/api/ (Django Ninja API endpoints)
- core/migrations/ (0003-0021: Insurance models migrations)
- core/templates/insurance/ (Insurance templates)

## Important Notes

1. **Database Configuration**: Make sure to update database settings for the new server
2. **Environment Variables**: Create `.env` file on the new server (not committed)
3. **Migrations**: Run migrations on the new server:
   ```bash
   python manage.py migrate --database=insurance
   ```
4. **Static Files**: Collect static files:
   ```bash
   python manage.py collectstatic
   ```

## Security Checklist

- [ ] Verify `.env` is in `.gitignore` (already done)
- [ ] Verify `local_settings.py` is in `.gitignore` (already done)
- [ ] Check for any hardcoded passwords or API keys
- [ ] Review database credentials in settings files
- [ ] Ensure sensitive data is not committed

