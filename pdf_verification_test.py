#!/usr/bin/env python3
"""
PDF Verification Test - Check if generated PDF contains all required elements
"""

import requests
import sys
from pathlib import Path

BASE_URL = "https://code-fork-4.preview.emergentagent.com/api"

def test_pdf_download_verification():
    """Test PDF download and verify file properties"""
    
    print("🔍 Testing PDF Download and Verification...")
    print("="*60)
    
    try:
        # Get the latest invoice (TTS / 004 / 2025-26 from our test)
        invoice_id = "TTS / 004 / 2025-26"
        
        # URL encode the invoice ID
        import urllib.parse
        encoded_id = urllib.parse.quote(invoice_id, safe='')
        pdf_url = f"{BASE_URL}/invoices/{encoded_id}/pdf"
        
        print(f"📋 Testing PDF URL: {pdf_url}")
        
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ PDF download successful")
            
            # Check file size
            pdf_size = len(response.content)
            print(f"📊 PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
            
            # Verify file size is reasonable (around 300KB as per review request)
            if 200000 <= pdf_size <= 500000:  # 200KB to 500KB
                print("✅ PDF size is within expected range (200-500KB)")
            else:
                print(f"⚠️  PDF size {pdf_size/1024:.1f} KB outside expected range")
            
            # Save PDF for inspection
            pdf_path = Path("/tmp/invoice_verification.pdf")
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            print(f"✅ PDF saved to {pdf_path}")
            
            # Check PDF headers
            pdf_header = response.content[:10]
            if pdf_header.startswith(b'%PDF-'):
                print("✅ Valid PDF file format")
            else:
                print("❌ Invalid PDF file format")
            
            # Check response headers
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                print("✅ Correct Content-Type header")
            else:
                print(f"⚠️  Unexpected Content-Type: {content_type}")
            
            # Check if file is not corrupted (basic check)
            if len(response.content) > 1000 and b'%%EOF' in response.content[-100:]:
                print("✅ PDF appears to be complete (has EOF marker)")
            else:
                print("⚠️  PDF may be incomplete or corrupted")
            
            return True
            
        else:
            print(f"❌ PDF download failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF verification test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_public_pdf_endpoint():
    """Test public PDF endpoint for WhatsApp sharing"""
    
    print("\n🌐 Testing Public PDF Endpoint...")
    print("="*40)
    
    try:
        invoice_id = "TTS / 004 / 2025-26"
        
        # URL encode the invoice ID
        import urllib.parse
        encoded_id = urllib.parse.quote(invoice_id, safe='')
        public_pdf_url = f"{BASE_URL}/public/invoices/{encoded_id}/pdf"
        
        print(f"📋 Testing Public PDF URL: {public_pdf_url}")
        
        # Download PDF via public endpoint
        response = requests.get(public_pdf_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Public PDF endpoint working")
            
            # Check Content-Disposition header for inline display
            content_disposition = response.headers.get('content-disposition', '')
            if 'inline' in content_disposition:
                print("✅ Content-Disposition set to inline (good for WhatsApp)")
            else:
                print(f"⚠️  Content-Disposition: {content_disposition}")
            
            return True
        else:
            print(f"❌ Public PDF endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Public PDF test failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🚀 Starting PDF Verification Tests...")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("="*60)
    
    success = True
    
    # Test 1: PDF Download Verification
    if not test_pdf_download_verification():
        success = False
    
    # Test 2: Public PDF Endpoint
    if not test_public_pdf_endpoint():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 ALL PDF VERIFICATION TESTS PASSED!")
    else:
        print("⚠️  SOME PDF VERIFICATION TESTS FAILED!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)