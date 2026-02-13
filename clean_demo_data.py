#!/usr/bin/env python3
"""Script to clean all demo data from MongoDB database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def clean_database():
    """Remove all demo data from the database"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🗑️  Cleaning demo data from database...")
    
    # Count before deletion
    tiles_count = await db.tiles.count_documents({})
    customers_count = await db.customers.count_documents({})
    invoices_count = await db.invoices.count_documents({})
    
    print(f"\n📊 Current database state:")
    print(f"   Tiles: {tiles_count}")
    print(f"   Customers: {customers_count}")
    print(f"   Invoices: {invoices_count}")
    
    # Delete all data
    tiles_deleted = await db.tiles.delete_many({})
    customers_deleted = await db.customers.delete_many({})
    invoices_deleted = await db.invoices.delete_many({})
    
    print(f"\n✅ Deleted:")
    print(f"   Tiles: {tiles_deleted.deleted_count}")
    print(f"   Customers: {customers_deleted.deleted_count}")
    print(f"   Invoices: {invoices_deleted.deleted_count}")
    
    print(f"\n✨ Database cleaned successfully!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_database())
