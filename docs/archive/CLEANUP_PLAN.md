# COMPREHENSIVE CLEANUP PLAN
# Date: 2025-07-03
# Action: Complete cleanup and verification of Django algo trading platform

## FILES TO DELETE (Test/Debug/Temporary Scripts):

### Test Scripts:
- test_angelone_auth.py
- test_angelone_connection.py  
- test_angelone_debug.py
- test_angel_auth.py
- test_db_access.py
- test_django_service.py (keep as it's useful for verification)
- test_mpin_auth.py
- test_smartapi_official.py
- test_all_methods.py
- test_admin.py

### Debug Scripts:
- debug_admin.py
- debug_symbols.py

### Check Scripts:
- check_all_tables.py
- check_apps.py
- check_config.py
- check_db.py
- verify_database.py

### Populate/Create Scripts (Fake Data):
- populate_market_data.py
- populate_nse_symbols.py
- populate_realistic_prices.py
- populate_real_symbols.py
- create_sample_buy_sell_data.py
- create_test_trading_data.py
- clean_fake_data.py

### Demo/Simple Scripts:
- demo_trading_process.py
- simple_angelone_test.py
- simple_table_check.py
- quick_test.py

### Duplicate/Old Scripts:
- angelone_real_filter.py
- real_angelone_nse_filter.py
- real_nse_filter_75_150.py
- real_price_filter.py
- filter_stocks_75_150.py
- get_stocks_75_100.py
- PRODUCTION_nse_filter.py

### Old Symbol Fetching Scripts:
- download_nse_symbols.py
- fetch_nse_symbols_direct.py
- fetch_nse_symbols_real.py
- get_nse_stocks.py
- list_all_nse_symbols.py
- list_all_tables.py
- list_angelone_symbols.py
- list_nse_real_api.py
- save_filtered_symbols.py

### Utility Scripts (Some to Keep):
- direct_angel_test.py (DELETE)
- final_admin_check.py (DELETE)
- force_admin_reload.py (DELETE)
- get_actual_nse_stocks.py (KEEP - used for symbol master)
- ngrok_auto.py (KEEP - useful for deployment)
- start.py (REVIEW - might be useful)

## JSON OUTPUT FILES TO ORGANIZE:
- Move all filtered_stocks_*.json to a results/ folder
- Move all real_nse_*.json to a results/ folder
- Keep nse_actual_stocks_*.json as it's the master symbol file

## FILES TO KEEP:
- smartapi_filter.py (MAIN WORKING SCRIPT)
- credentials.py (ESSENTIAL)
- manage.py (DJANGO)
- requirements.txt (ESSENTIAL)
- README.md, LICENSE (DOCUMENTATION)
- All Django app folders (angel_api/, core/, portfolio/, trading/)
- nse_actual_stocks_20250703_214624.json (SYMBOL MASTER)

## VERIFICATION CHECKLIST:
1. Ensure Django service works
2. Ensure management commands work
3. Ensure smartapi_filter.py works
4. Verify all dependencies in requirements.txt
5. Clean up __pycache__ folders
6. Update .gitignore if needed
