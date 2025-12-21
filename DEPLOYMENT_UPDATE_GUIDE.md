# Deployment Update Guide

## Overview
This guide helps you update your existing deployed system with the latest features including check-in/check-out functionality and analytics logging.

## Prerequisites
- Existing face recognition system deployed
- PostgreSQL database access
- Python environment with dependencies installed
- Server access (SSH or direct)

---

## Step 1: Backup Your Database

**IMPORTANT: Always backup before running migrations!**

```bash
# Backup your database
pg_dump -U postgres -d face_recognition > backup_$(date +%Y%m%d_%H%M%S).sql

# Or if using Docker
docker exec your_postgres_container pg_dump -U postgres face_recognition > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Step 2: Pull Latest Code

```bash
# Navigate to your project directory
cd /path/to/face-recognition-system

# Pull latest changes (if using git)
git pull origin main

# Or copy updated files to server
```

---

## Step 3: Run Database Migrations

### Migration 1: Add Check-In/Check-Out Columns

This adds `check_in_time` and `check_out_time` columns to the attendance table.

```bash
python3 migrate_add_checkin_checkout.py
```

**What it does:**
- Adds `check_in_time` column (TIMESTAMP WITH TIME ZONE)
- Adds `check_out_time` column (TIMESTAMP WITH TIME ZONE)
- Migrates existing data: sets `check_in_time = marked_at` for existing records

**Expected Output:**
```
✅ Successfully added check_in_time and check_out_time columns
✅ Migrated existing records: check_in_time = marked_at
```

---

### Migration 2: Create Analytics Log Table

This creates a new table to track all system events (registrations, check-ins, check-outs).

```bash
python3 migrate_add_analytics_log.py
```

**What it does:**
- Creates `analytics_log` table with columns:
  - `id`, `event_type`, `person_id`, `emp_id`, `name`, `region`
  - `timestamp` (IST), `date`, `event_metadata` (JSON)
- Creates indexes for fast queries
- No data migration needed (new table)

**Expected Output:**
```
✅ Successfully created analytics_log table with indexes
```

---

### Migration 3: Rename Metadata Column (if needed)

If you already ran the analytics migration, you may need to rename the column:

```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(dbname='face_recognition', user='postgres', password='postgres', host='localhost', port='5432')
cur = conn.cursor()
cur.execute('ALTER TABLE analytics_log RENAME COLUMN metadata TO event_metadata;')
conn.commit()
print('✅ Column renamed successfully')
conn.close()
"
```

---

## Step 4: Verify Database Changes

```bash
# Check attendance table structure
psql -U postgres -d face_recognition -c "\d attendance"

# Check analytics_log table structure
psql -U postgres -d face_recognition -c "\d analytics_log"

# Verify data
psql -U postgres -d face_recognition -c "SELECT COUNT(*) FROM attendance;"
psql -U postgres -d face_recognition -c "SELECT COUNT(*) FROM analytics_log;"
```

---

## Step 5: Restart Application

```bash
# If using systemd
sudo systemctl restart face-recognition

# If using PM2
pm2 restart face-recognition

# If running manually
# Stop the current process (Ctrl+C)
python3 main.py --host 0.0.0.0 --port 8000

# Or with uvicorn
uvicorn src.api.advanced_fastapi_app:app --host 0.0.0.0 --port 8000
```

---

## Step 6: Clear Browser Cache

**Important:** Users must hard refresh their browsers to get the updated UI.

- **Chrome/Edge**: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Firefox**: `Ctrl + F5` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Safari**: `Cmd + Option + R` (Mac)

---

## Step 7: Verify New Features

### Test Check-In/Check-Out
1. Go to **Live Recognition** tab
2. Start camera and detect a face
3. Click "Check In" → Should show success with IST timestamp
4. Detect same person again → Should show "Check Out" button
5. Click "Check Out" → Should show both check-in and check-out times

### Test Analytics
1. Go to **Analytics** tab (Person Registration section)
2. Select date range (defaults to last 7 days)
3. Click "Load Analytics"
4. Should see:
   - Total Registrations count
   - Total Check-Ins count
   - Total Check-Outs count
   - Daily breakdown table

### Test Attendance Records
1. Go to **Analytics** tab → Attendance Records section
2. Select a date
3. Click "View Attendance"
4. Should see:
   - Check-In column with times
   - Check-Out column with times or "Not checked out"
   - Delete button for each record

---

## Rollback Instructions (If Needed)

If something goes wrong, you can rollback:

```bash
# Restore from backup
psql -U postgres -d face_recognition < backup_YYYYMMDD_HHMMSS.sql

# Or rollback specific migrations
psql -U postgres -d face_recognition -c "ALTER TABLE attendance DROP COLUMN check_in_time, DROP COLUMN check_out_time;"
psql -U postgres -d face_recognition -c "DROP TABLE analytics_log;"
```

---

## Migration Files Summary

| File | Purpose | Required? |
|------|---------|-----------|
| `migrate_add_checkin_checkout.py` | Add check-in/check-out columns | ✅ Yes |
| `migrate_add_analytics_log.py` | Create analytics log table | ✅ Yes |

**Note:** After running migrations successfully, you can delete these files or keep them for reference.

---

## New Features Added

### 1. Check-In/Check-Out System
- First recognition → "Check In" button
- Second recognition → "Check Out" button  
- Third recognition → "Already completed" message
- All timestamps in IST (Asia/Kolkata)

### 2. Analytics Dashboard
- Track registrations, check-ins, check-outs
- Date range filtering
- Region filtering
- Daily breakdown statistics

### 3. Improved Live Recognition
- Camera keeps running after detection
- Multiple people can be detected simultaneously
- No auto check-in (user must click button)
- Detected people remain visible until action taken

### 4. Attendance Records Enhancement
- Shows check-in and check-out times separately
- Delete button to remove incorrect records
- All times displayed in IST

---

## Troubleshooting

### Issue: Import errors about Date or JSON
**Solution:** Already fixed in code. Ensure you have latest `src/models/database.py`

### Issue: "metadata" column error
**Solution:** Run the rename command in Step 3, Migration 3

### Issue: Old UI still showing
**Solution:** Hard refresh browser (Ctrl+Shift+R)

### Issue: Analytics showing 0 counts
**Solution:** Normal for new installation. Counts will increase as you use the system.

### Issue: Check-in button not appearing
**Solution:** 
1. Hard refresh browser
2. Check browser console for errors (F12)
3. Verify API endpoint: `GET /api/attendance/check?emp_id=XXX`

---

## Post-Deployment Checklist

- [ ] Database backup created
- [ ] Migration 1 completed (check-in/check-out columns)
- [ ] Migration 2 completed (analytics_log table)
- [ ] Application restarted successfully
- [ ] Browser cache cleared
- [ ] Check-in/check-out tested
- [ ] Analytics dashboard tested
- [ ] Attendance records showing correctly
- [ ] No errors in server logs

---

## Support

If you encounter issues:
1. Check server logs: `tail -f /path/to/logs/app.log`
2. Check database: `psql -U postgres -d face_recognition`
3. Verify all migrations ran successfully
4. Ensure browser cache is cleared

---

## Summary

**Required Steps:**
1. ✅ Backup database
2. ✅ Run `migrate_add_checkin_checkout.py`
3. ✅ Run `migrate_add_analytics_log.py`
4. ✅ Restart application
5. ✅ Hard refresh browser

**Time Required:** ~5-10 minutes

**Downtime:** ~1-2 minutes (during restart)

**Risk Level:** Low (migrations are additive, no data loss)
