"""
Sellauth Code Generator - Generate multiple redemption codes for the web redeem panel

Supports both PostgreSQL (unified database) and SQLite (local fallback).
Set DATABASE_URL environment variable to use PostgreSQL.
"""
import sys
import os
import random
import string
from dotenv import load_dotenv

# Load environment variables from .env.local if it exists
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Make sure we can import RedeemDatabase from the same folder
from redeem_db import RedeemDatabase


def generate_random_code(prefix: str = "", length: int = 16) -> str:
    """Generate a secure random alphanumeric code"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    formatted = '-'.join([random_part[i:i+4] for i in range(0, len(random_part), 4)])

    if prefix:
        return f"{prefix.upper()}-{formatted.upper()}"
    return formatted.upper()


def get_database_connection() -> str:
    """Return PostgreSQL URL or fallback to SQLite"""
    # Try to get PostgreSQL URL from environment
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"🐘 Using PostgreSQL database (codes will be instantly available on Discord bot and website)")
        return db_url
    
    # Fallback to SQLite
    print(f"📂 Using SQLite database (local only - you'll need to push to GitHub for website)")
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'redeem_codes.db')


def generate_codes(
    count: int,
    service_id: int,
    quantity: int,
    platform: str,
    service_type: str,
    requirements: str = "",
    expiry_days: int = 30,
    prefix: str = "",
    has_refill: bool = False
):
    """Generate multiple codes and add to the database"""
    db_connection = get_database_connection()
    db = RedeemDatabase(db_connection)

    print(f"\n🎫 Generating {count} codes for Sellauth panel...")
    print(f"📋 Service ID: {service_id}")
    print(f"📊 Quantity: {quantity}")
    print(f"🌐 Platform: {platform}")
    print(f"🎯 Type: {service_type}")
    print(f"⏰ Expiry: {expiry_days} days")
    if prefix:
        print(f"🏷️  Prefix: {prefix}")
    print("-" * 50)

    generated = []
    failed = []

    for i in range(count):
        code = generate_random_code(prefix=prefix)

        success = db.add_code(
            code=code,
            service_id=service_id,
            quantity=quantity,
            platform=platform,
            service_type=service_type,
            requirements=requirements,
            expiry_days=expiry_days,
            has_refill=has_refill
        )

        if success:
            generated.append(code)
            print(f"✅ {i+1}/{count}: {code}")
        else:
            failed.append(code)
            print(f"❌ {i+1}/{count}: {code} (already exists, retrying...)")
            retry_count = 0
            while retry_count < 5:
                code = generate_random_code(prefix=prefix)
                success = db.add_code(
                    code=code,
                    service_id=service_id,
                    quantity=quantity,
                    platform=platform,
                    service_type=service_type,
                    requirements=requirements,
                    expiry_days=expiry_days,
                    has_refill=has_refill
                )
                if success:
                    generated.append(code)
                    print(f"✅ {i+1}/{count}: {code} (retry successful)")
                    break
                retry_count += 1

    print("-" * 50)
    print(f"\n✅ Successfully generated: {len(generated)}/{count}")
    if failed:
        print(f"❌ Failed: {len(failed)}")

    # Save to file (for your own records) in For-Sellauth/data
    if generated:
        filename = f"codes_{platform}_{service_type}_{count}.txt"
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Generated Codes - {platform.title()} {service_type.title()}\n")
            f.write(f"Service ID: {service_id}\n")
            f.write(f"Quantity: {quantity}\n")
            f.write(f"Expiry: {expiry_days} days\n")
            f.write("-" * 50 + "\n\n")
            for code in generated:
                f.write(f"{code}\n")

        print(f"\n💾 Codes saved to: {filepath}")

    return generated


def interactive_mode():
    """Interactive mode for generating codes"""
    print("\n" + "=" * 50)
    print("🎫 Sellauth Code Generator - Interactive Mode")
    print("=" * 50 + "\n")

    try:
        count = int(input("How many codes to generate? "))
        service_id = int(input("Service ID (from SMB Panel): "))
        quantity = int(input("Quantity per code: "))
        platform = input("Platform (youtube/instagram/tiktok/etc): ").lower()
        service_type = input("Service type (subscribers/views/likes/etc): ").lower()
        requirements = input("Requirements (optional, press Enter to skip): ")
        expiry_days = int(input("Expiry days (default 30): ") or "30")
        has_refill_input = input("Has refill? (y/n, default n): ").strip().lower() or 'n'
        has_refill = has_refill_input in ('y', 'yes')
        prefix = input("Code prefix (optional, press Enter to skip): ").upper()

        print("\n" + "=" * 50)
        print("📋 Summary:")
        print(f"  Codes: {count}")
        print(f"  Service ID: {service_id}")
        print(f"  Quantity: {quantity}")
        print(f"  Platform: {platform}")
        print(f"  Type: {service_type}")
        print(f"  Expiry: {expiry_days} days")
        print(f"  Refill: {'Yes' if has_refill else 'No'}")
        if prefix:
            print(f"  Prefix: {prefix}")
        print("=" * 50)

        confirm = input("\nGenerate these codes? (yes/no): ").lower()

        if confirm in ['yes', 'y']:
            codes = generate_codes(
                count=count,
                service_id=service_id,
                quantity=quantity,
                platform=platform,
                service_type=service_type,
                requirements=requirements,
                expiry_days=expiry_days,
                prefix=prefix,
                has_refill=has_refill
            )

            print(f"\n🎉 Done! Generated {len(codes)} codes.")
        else:
            print("\n❌ Cancelled.")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        # Usage: python generate_codes_sellauth.py <count> <service_id> <quantity> <platform> <service_type> [prefix]
        try:
            count = int(sys.argv[1])
            service_id = int(sys.argv[2])
            quantity = int(sys.argv[3])
            platform = sys.argv[4].lower()
            service_type = sys.argv[5].lower()
            prefix = sys.argv[6].upper() if len(sys.argv) > 6 else ""

            generate_codes(
                count=count,
                service_id=service_id,
                quantity=quantity,
                platform=platform,
                service_type=service_type,
                prefix=prefix
            )
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nUsage: python generate_codes_sellauth.py <count> <service_id> <quantity> <platform> <service_type> [prefix]")
            print("Example: python generate_codes_sellauth.py 10 15400 10 youtube subscribers TEST")
    else:
        # Interactive mode
        interactive_mode()
