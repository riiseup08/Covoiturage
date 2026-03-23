# Demo Account Setup Guide

This guide explains how to create test/demo accounts for pilot testing of Covoiturage.

## Quick Start (1 minute)

```bash
cd c:\Users\pokam\Downloads\Covoiturage

# Create demo accounts + sample data
python manage.py create_demo_data

# Clear existing demo data and recreate
python manage.py create_demo_data --clear
```

## What Gets Created

### Demo Users

The command creates 4 test accounts:

| Username | Password | Role | Phone |
|----------|----------|------|-------|
| `demo_driver` | `DemoPass123!` | Driver | +237 6 74 12 34 56 |
| `demo_passenger1` | `DemoPass123!` | Passenger | +237 6 99 45 67 89 |
| `demo_passenger2` | `DemoPass123!` | Passenger | +237 6 70 12 34 56 |
| `demo_passenger3` | `DemoPass123!` | Passenger | +237 6 50 98 76 54 |

### Demo Trips (Voyages)

3 sample carpools are created:

1. **Douala → Limbe** (3,500 XAF per seat)
   - From: Akwa Market
   - To: Limbe Beach
   - 3 available seats
   - Accepts: Mobile Money + Cash

2. **Yaoundé → Mvogue** (1,500 XAF per seat)
   - From: Kennedy Avenue
   - To: Mvogue
   - 2 available seats
   - Accepts: Mobile Money only

3. **Buea → Molyko** (2,000 XAF per seat)
   - From: Government School Junction
   - To: Molyko
   - 4 available seats
   - Accepts: Cash only

### Demo Requests

Each passenger has a ride request auto-matched with available trips.

## Login & Test Flow

### 1. Web Interface
```
URL: http://localhost:8000/admin/
Username: admin
Password: (set during initial setup)
```

### 2. Mobile App (Web)
```
URL: http://localhost:8081
Login as: demo_driver / DemoPass123!
```

### 3. Test Driver Flow
- ✓ Login as `demo_driver`
- ✓ View available requests in Matches tab
- ✓ Accept trip requests
- ✓ View wallet balance (Driver → Wallet)
- ✓ Test cash payment confirmation

### 4. Test Passenger Flow
- ✓ Login as `demo_passenger1`
- ✓ Search available trips
- ✓ Request a ride
- ✓ Match with `demo_driver`
- ✓ Test payment confirmation screen
- ✓ Pay for trip (cash or Mobile Money)

## Testing Scenarios

### Scenario 1: Complete Cash Ride
```
1. Passenger: demo_passenger1
   - Login
   - Search trips
   - Request Douala-Limbe (1 seat)

2. Driver: demo_driver
   - Accept passenger request
   - View match

3. Passenger:
   - Confirm payment (cash option)
   - See transaction confirmation

4. Driver:
   - Confirm cash receipt
   - Check wallet (commission deducted)
```

### Scenario 2: Mobile Money Payment
```
1. Passenger: demo_passenger2
   - Request Yaoundé-Mvogue trip

2. Driver:
   - Accept request

3. Passenger:
   - Pay via Mobile Money (MTN MoMo option)
   - See transaction confirmation

4. Check payment status in Payments tab
```

### Scenario 3: Wallet Top-up
```
1. Driver: demo_driver
   - Navigate to Wallet
   - Click "Add Balance"
   - Select 5,000 XAF
   - Confirm top-up
   - Check transaction history
```

## Database State

After running `create_demo_data`:

```
Users: 4 demo accounts (+ your admin user)
Profiles: 4 profiles with phone verified
Voyages: 3 sample trips
Demandes: 3 ride requests
Correspondance: 3 auto-matched pairs
```

### To Clear Everything

```bash
# Option 1: Just clear demo accounts (keep other data)
python manage.py create_demo_data --clear

# Option 2: Full database reset
python manage.py migrations zero covoiturage
python manage.py migrate
python manage.py create_demo_data
```

## API Testing

Test endpoints directly:

```bash
# 1. Login as demo driver
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_driver","password":"DemoPass123!"}'

# Response: {"token":"abc123...","user_id":5,...}

# 2. Get my wallet
curl -X GET http://localhost:8000/api/wallet/balance/ \
  -H "Authorization: Token abc123..."

# 3. Request topup
curl -X POST http://localhost:8000/api/wallet/topup/request/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "amount":5000,
    "provider":"mtn",
    "phone_number":"237674123456"
  }'
```

## Performance Testing

Test on low-bandwidth network:

```bash
# Chrome DevTools:
# 1. Open Network tab
# 2. Set throttling to "Slow 3G"
# 3. Login and navigate through app
# 4. Check load times (target: < 3s per page)

# Or use Django Debug Toolbar
# pip install django-debug-toolbar
```

## Cleanup

To remove demo accounts:

```bash
# Via management command
python manage.py create_demo_data --clear

# Via Django admin
# Login to http://localhost:8000/admin/
# Delete users starting with "demo_"
```

## Troubleshooting

### Demo accounts not appearing

```bash
# Verify they were created
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.filter(username__startswith='demo_').count()
# Should return 4

# If 0, run create_demo_data again
```

### Payments not working

Ensure database migration ran:
```bash
python manage.py migrate
```

### Can't login

Check profile exists:
```bash
python manage.py shell
>>> from covoiturage.models import Profile
>>> Profile.objects.filter(user__username='demo_driver').exists()
# Should return True
```

## Next Steps for Pilot

1. **Share credentials** with pilot testers
2. **Set realistic prices** (current are for testing)
3. **Test on actual 3G/4G** network if possible
4. **Collect feedback** via form or chat
5. **Adjust UI/UX** based on feedback
6. **Prepare for public launch**

---

**Need help?** Check [README.md](./README.md) or open an issue on GitHub.
