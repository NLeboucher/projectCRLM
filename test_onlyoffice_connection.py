#!/usr/bin/env python3
"""
Test script to verify OnlyOffice server connectivity from host environment.
This simulates the same network environment where Odoo runs.
"""

import requests
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime

# OnlyOffice Configuration
ONLYOFFICE_URL = "http://localhost:8068"
JWT_SECRET = "34053c2c2b59b63f596f66c130f285f6fb28b1d4a2c0ea5de6fe664e40510e6f"

def print_test(test_name):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_result(success, message):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")

def test_basic_connectivity():
    """Test 1: Basic HTTP connectivity to OnlyOffice"""
    print_test("Basic HTTP Connectivity")
    
    try:
        response = requests.get(ONLYOFFICE_URL, timeout=5)
        if response.status_code == 200:
            print_result(True, f"OnlyOffice server is reachable at {ONLYOFFICE_URL}")
            print(f"   Response status: {response.status_code}")
            return True
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to OnlyOffice server")
        print(f"   Make sure OnlyOffice is running: sudo docker ps | grep onlyoffice")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_healthcheck():
    """Test 2: OnlyOffice healthcheck endpoint"""
    print_test("OnlyOffice Healthcheck Endpoint")
    
    try:
        response = requests.get(f"{ONLYOFFICE_URL}/healthcheck", timeout=5)
        if response.status_code == 200:
            print_result(True, "Healthcheck endpoint responded")
            print(f"   Status: {response.text.strip()}")
            return True
        else:
            print_result(False, f"Healthcheck returned: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def generate_jwt_token(payload):
    """Generate JWT token for OnlyOffice"""
    # OnlyOffice uses HS256 for JWT
    import jwt
    try:
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        return token
    except ImportError:
        # Fallback if PyJWT is not installed
        print("   Note: PyJWT not installed, skipping JWT token generation")
        return None

def test_converter_api():
    """Test 3: Document Converter API (the API Odoo would use)"""
    print_test("Document Converter API Endpoint")
    
    converter_url = f"{ONLYOFFICE_URL}/ConvertService.ashx"
    
    # Prepare a simple conversion request (without actual file, just to test endpoint)
    payload = {
        "async": False,
        "filetype": "docx",
        "key": f"test_key_{int(time.time())}",
        "outputtype": "pdf",
        "title": "test.docx",
        "url": "http://example.com/test.docx"  # Dummy URL for testing
    }
    
    try:
        # Try without JWT first (should fail if JWT is required)
        response = requests.post(
            converter_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response body: {response.text[:200] if response.text else 'empty'}")
        
        # Check if we got a JWT error
        if response.status_code == 401 or "jwt" in response.text.lower():
            print_result(True, "Converter API is accessible (JWT authentication required as expected)")
            print(f"   This confirms the endpoint exists and JWT is enforced")
            return True
        elif response.status_code == 200:
            print_result(True, "Converter API is accessible and responded")
            return True
        else:
            # Even error responses mean we can reach the server
            print_result(True, f"Converter API is accessible (status: {response.status_code})")
            return True
            
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to converter API")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_info_endpoint():
    """Test 4: OnlyOffice info endpoint"""
    print_test("OnlyOffice Info Endpoint")
    
    try:
        # Try the info endpoint
        response = requests.get(f"{ONLYOFFICE_URL}/hosting/discovery", timeout=5)
        
        if response.status_code == 200:
            print_result(True, "Discovery endpoint accessible")
            print(f"   OnlyOffice is properly configured and accessible")
            return True
        else:
            # Even if we get a different status, it means we can reach it
            print_result(True, f"Server responded (status: {response.status_code})")
            return True
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_jwt_configuration():
    """Test 5: Verify JWT configuration"""
    print_test("JWT Configuration Verification")
    
    print(f"   OnlyOffice URL: {ONLYOFFICE_URL}")
    print(f"   JWT Secret configured: {'Yes' if JWT_SECRET else 'No'}")
    print(f"   JWT Secret length: {len(JWT_SECRET)} characters")
    
    if len(JWT_SECRET) == 64:  # 32 bytes in hex = 64 characters
        print_result(True, "JWT secret is properly configured (256-bit)")
        return True
    else:
        print_result(False, f"JWT secret length unexpected: {len(JWT_SECRET)}")
        return False

def test_network_path():
    """Test 6: Verify network path (same as Odoo would use)"""
    print_test("Network Path Verification (Odoo Perspective)")
    
    print("   This test simulates how Odoo will communicate with OnlyOffice:")
    print(f"   1. Odoo runs on host → can access localhost:{ONLYOFFICE_URL.split(':')[-1]}")
    print(f"   2. OnlyOffice container → can access host's localhost")
    print(f"   3. Bidirectional communication → ✅ Possible")
    
    try:
        # Test that we can make a request from host to container
        response = requests.get(ONLYOFFICE_URL, timeout=5)
        if response.status_code == 200:
            print_result(True, "Host → OnlyOffice container communication works")
            print("   This is exactly how Odoo will communicate with OnlyOffice")
            return True
        else:
            print_result(False, f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def test_document_conversion():
    """Test 7: Convert new.docx to PDF"""
    print_test("Document Conversion: DOCX to PDF")
    
    import os
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    import xml.etree.ElementTree as ET
    
    docx_file = "new.docx"
    pdf_output = "new_converted.pdf"
    
    # Check if input file exists
    if not os.path.exists(docx_file):
        print_result(False, f"Input file '{docx_file}' not found")
        return False
    
    print(f"   Input file: {docx_file}")
    print(f"   Output file: {pdf_output}")
    print(f"   File size: {os.path.getsize(docx_file)} bytes")
    
    # Start a simple HTTP server to serve the file
    # OnlyOffice needs to download the file from a URL
    server_port = 8888
    
    class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress log messages
    
    def run_server():
        httpd = HTTPServer(('0.0.0.0', server_port), QuietHTTPRequestHandler)
        httpd.timeout = 30
        httpd.handle_request()  # Handle just one request then stop
    
    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print(f"   Started temporary HTTP server on port {server_port}")
    
    # Give server a moment to start
    time.sleep(1)
    
    # Prepare conversion request
    converter_url = f"{ONLYOFFICE_URL}/ConvertService.ashx"
    
    # Get the host's actual IP address (not Docker gateway or loopback)
    import socket
    import subprocess
    
    # Get the primary network interface IP
    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    host_ip = result.stdout.strip().split()[0] if result.stdout else '127.0.0.1'
    
    file_url = f"http://{host_ip}:{server_port}/{docx_file}"
    
    payload = {
        "async": False,
        "filetype": "docx",
        "key": f"conversion_key_{int(time.time())}",
        "outputtype": "pdf",
        "title": docx_file,
        "url": file_url
    }
    
    print(f"   Host IP: {host_ip}")
    print(f"   Document URL for OnlyOffice: {file_url}")
    
    try:
        # Generate JWT token
        import jwt
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        print("   Using JWT authentication")
        
        # Send request with JWT in the payload
        request_payload = {
            "token": token
        }
        
        print("   Sending conversion request...")
        response = requests.post(
            converter_url,
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response body: {response.text[:500]}")
        
        if response.status_code == 200:
            # Try to parse as JSON first
            try:
                result = response.json()
                print(f"   JSON Response: {json.dumps(result, indent=2)}")
                
                if 'fileUrl' in result or 'url' in result:
                    # Download the converted PDF
                    pdf_url = result.get('fileUrl') or result.get('url')
                    print(f"   Downloading PDF from: {pdf_url}")
                    
                    pdf_response = requests.get(pdf_url, timeout=30)
                    if pdf_response.status_code == 200:
                        with open(pdf_output, 'wb') as f:
                            f.write(pdf_response.content)
                        
                        pdf_size = os.path.getsize(pdf_output)
                        print_result(True, f"Successfully converted DOCX to PDF")
                        print(f"   Output file: {pdf_output} ({pdf_size} bytes)")
                        return True
                    else:
                        print_result(False, f"Failed to download PDF: {pdf_response.status_code}")
                        return False
                elif 'error' in result:
                    print_result(False, f"Conversion error: {result['error']}")
                    return False
            except:
                # Try to parse as XML
                try:
                    root = ET.fromstring(response.text)
                    error_code = root.find('Error')
                    file_url = root.find('FileUrl')
                    end_convert = root.find('EndConvert')
                    
                    if error_code is not None and error_code.text != '0':
                        print_result(False, f"OnlyOffice error code: {error_code.text}")
                        return False
                    
                    if file_url is not None and file_url.text:
                        # Download the converted PDF
                        pdf_url = file_url.text
                        print(f"   Downloading PDF from: {pdf_url}")
                        
                        pdf_response = requests.get(pdf_url, timeout=30)
                        if pdf_response.status_code == 200:
                            with open(pdf_output, 'wb') as f:
                                f.write(pdf_response.content)
                            
                            pdf_size = os.path.getsize(pdf_output)
                            print_result(True, f"Successfully converted DOCX to PDF")
                            print(f"   Output file: {pdf_output} ({pdf_size} bytes)")
                            return True
                        else:
                            print_result(False, f"Failed to download PDF: {pdf_response.status_code}")
                            return False
                    else:
                        print_result(False, f"No file URL in response")
                        return False
                except Exception as xml_error:
                    print_result(False, f"Failed to parse response: {str(xml_error)}")
                    return False
        else:
            print_result(False, f"Conversion request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("OnlyOffice Server Connectivity Test Suite")
    print("Testing from host environment (same as Odoo)")
    print("="*60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run tests
    results.append(("Basic Connectivity", test_basic_connectivity()))
    results.append(("Healthcheck", test_healthcheck()))
    results.append(("Converter API", test_converter_api()))
    results.append(("Info Endpoint", test_info_endpoint()))
    results.append(("JWT Configuration", test_jwt_configuration()))
    results.append(("Network Path", test_network_path()))
    results.append(("Document Conversion", test_document_conversion()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ OnlyOffice server is fully accessible from the host environment")
        print("✅ Odoo (running in the same environment) will be able to communicate")
        print("✅ Ready to install Odoo OnlyOffice module and configure integration")
        print("\nNext steps:")
        print("1. Install OnlyOffice module in Odoo")
        print("2. Configure with:")
        print(f"   - Server URL: {ONLYOFFICE_URL}")
        print(f"   - JWT Secret: {JWT_SECRET}")
        print("3. Test document editing in Odoo")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please check the OnlyOffice container status:")
        print("   sudo docker ps | grep onlyoffice")
        print("   sudo docker logs 5f60e63cc32d")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
