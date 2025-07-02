#!/usr/bin/env python
"""Verify all Django models and database tables are working correctly."""

import os
import sys
import django
from django.apps import apps

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manage')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def verify_models_and_tables():
    """Verify all models are properly registered and accessible."""
    
    print("=" * 60)
    print("🔍 DJANGO MODELS & TABLES VERIFICATION")
    print("=" * 60)
    
    # Get all apps
    app_configs = apps.get_app_configs()
    
    total_models = 0
    working_models = 0
    
    for app_config in app_configs:
        app_label = app_config.label
        if app_label in ['portfolio', 'trading', 'angel_api', 'core']:
            models = app_config.get_models()
            
            if models:
                print(f"\n📦 {app_label.upper()} APP:")
                print("-" * 40)
                
                for model in models:
                    model_name = model.__name__
                    table_name = model._meta.db_table
                    total_models += 1
                    
                    try:
                        # Try to query the model (this will fail if table doesn't exist)
                        count = model.objects.count()
                        working_models += 1
                        print(f"   ✅ {model_name:<20} -> {table_name:<30} ({count} records)")
                    except Exception as e:
                        print(f"   ❌ {model_name:<20} -> {table_name:<30} ERROR: {str(e)}")
    
    print(f"\n📊 VERIFICATION SUMMARY:")
    print(f"   Total models checked: {total_models}")
    print(f"   Working models: {working_models}")
    print(f"   Success rate: {(working_models/total_models)*100:.1f}%")
    
    if working_models == total_models:
        print("\n🎉 ALL MODELS AND TABLES ARE WORKING CORRECTLY!")
        
        # Test creating a portfolio to ensure write access works
        from django.contrib.auth.models import User
        from portfolio.models import Portfolio
        
        # Check if test user exists
        test_user = User.objects.filter(username='admin').first()
        if test_user:
            portfolio, created = Portfolio.objects.get_or_create(
                user=test_user,
                defaults={
                    'name': 'Test Portfolio',
                    'current_balance': 50000.00
                }
            )
            status = "created" if created else "exists"
            print(f"\n💼 Test Portfolio: {status} - Balance: ₹{portfolio.current_balance}")
            print(f"   📝 Portfolio ID: {portfolio.id}")
            print(f"   👤 User: {portfolio.user.username}")
            
            return True
    else:
        print(f"\n❌ {total_models - working_models} models have issues!")
        return False

if __name__ == '__main__':
    success = verify_models_and_tables()
    if success:
        print("\n✅ Database verification completed successfully!")
    else:
        print("\n❌ Database verification failed!")
        sys.exit(1)
