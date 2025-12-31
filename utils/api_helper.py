"""
API Helper for Jenkins Integration
Tracks test execution and sends data to backend API

Usage:
    This module is automatically integrated via conftest.py
    No manual intervention needed in test files
    
Environment Variables:
    API_BASE_URL: Backend API URL (default: ngrok URL)
    API_TOKEN: API authentication token
    ORG_ID: Organization ID
    CREATED_BY: User ID
    BUILD_NUMBER: Jenkins build number
    JOB_NAME: Jenkins job name
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class APIHelper:
    """
    Handles API integration for tracking test execution in Jenkins
    
    Flow:
        1. before_all_tests() -> API-1: Create Pipeline Run
        2. after_each_test() -> API-3: Create Test Case (x N tests)
        3. after_all_tests() -> API-4: Update Pipeline Run
    """
    
    def __init__(self):
        # Detect Jenkins environment
        self.is_jenkins = os.getenv('JENKINS_HOME') is not None or os.getenv('BUILD_NUMBER') is not None
        
        # API Configuration
        self.api_base_url = os.getenv('API_BASE_URL', 'https://unsobering-maribeth-hokey.ngrok-free.dev')
        self.api_token = os.getenv('API_TOKEN', 'your-api-token-here')
        
        # Jenkins Environment Variables
        self.job_name = os.getenv('JOB_NAME', 'Unknown Job')
        self.build_number = os.getenv('BUILD_NUMBER', '0')
        self.build_url = os.getenv('BUILD_URL', '')
        self.git_branch = os.getenv('GIT_BRANCH', 'main')
        self.git_commit = os.getenv('GIT_COMMIT', 'unknown')
        
        # Organization & User IDs
        self.org_id = os.getenv('ORG_ID', '374060a8-925c-49aa-8495-8a823949f3e0')
        self.created_by = os.getenv('CREATED_BY', 'c9279b2d-701c-48eb-9122-fbeae465771c')
        
        # Execution State
        self.pipeline_run_id: Optional[str] = None
        self.test_results = []
        self.suite_start_time = None
        
        # Statistics
        self.api_call_count = {
            'api-1': 0,
            'api-3': 0,
            'api-4': 0
        }
        
    def before_all_tests(self):
        """
        API-1: Create Pipeline Run (Before All Tests)
        
        Called once at the start of test session
        Creates a new pipeline run in the backend
        """
        if not self.is_jenkins:
            logger.info("⚠️  Local run detected - Skipping API calls")
            logger.info(f"    To enable API calls, set BUILD_NUMBER environment variable")
            return
        
        self.suite_start_time = time.time()
        
        try:
            logger.info("")
            logger.info("=" * 63)
            logger.info("📡 API-1: Creating Pipeline Run")
            logger.info("=" * 63)
            
            payload = {
                "name": f"{self.job_name} - Build #{self.build_number}",
                "repo_name": "Python-Pylenium-Web",
                "environment": "qa",
                "org": self.org_id,
                "created_by": self.created_by,
                "build_number": int(self.build_number),
                "build_url": self.build_url,
                "git_branch": self.git_branch,
                "git_commit": self.git_commit,
                "status": "running",
                "started_at": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"📤 Request: POST {self.api_base_url}/api/pipeline-runs/")
            response = self._post_request("/api/pipeline-runs/", payload)
            
            if response and 'pipeline_run' in response:
                pipeline_run = response['pipeline_run']
                if 'run_id' in pipeline_run:
                    self.pipeline_run_id = pipeline_run['run_id']
                    self.api_call_count['api-1'] += 1
                    logger.info("")
                    logger.info("✅ API-1 SUCCESS: Pipeline Run Created")
                    logger.info(f"🆔 Pipeline Run ID: {self.pipeline_run_id}")
                    logger.info(f"📊 Build: #{self.build_number}")
                    logger.info(f"🌿 Branch: {self.git_branch}")
                else:
                    logger.error("❌ API-1 ERROR: 'run_id' not found in pipeline_run")
                    logger.error(f"    Response: {response}")
            else:
                logger.error("❌ API-1 ERROR: Invalid response structure")
                logger.error(f"    Response: {response}")
            
            logger.info("=" * 63)
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ API-1 ERROR: {str(e)}")
            import traceback
            logger.error(f"    Traceback: {traceback.format_exc()}")
    
    def after_each_test(self, test_name: str, status: str, duration: float, error_message: Optional[str] = None):
        """
        API-3: Create Test Case (After Each Test)
        
        Called after each individual test completes
        Sends test result to backend
        
        Args:
            test_name: Name of the test (e.g., "test_login_success")
            status: Test status - 'passed', 'failed', or 'skipped'
            duration: Test execution time in seconds
            error_message: Error message if test failed (optional)
        """
        # Store result locally
        test_result = {
            "name": test_name,
            "status": status.upper(),
            "duration": duration,
            "error_message": error_message
        }
        self.test_results.append(test_result)
        
        # Log locally regardless of Jenkins
        status_emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⊘"
        logger.info(f"{status_emoji} {test_name} | {status.upper()} ({duration:.2f}s)")
        
        if not self.is_jenkins or not self.pipeline_run_id:
            return
        
        try:
            # Convert duration to milliseconds
            duration_ms = int(duration * 1000)
            
            # Prepare payload
            payload = {
                "run": self.pipeline_run_id,  # Field name is "run" not "pipeline_run"
                "name": test_name,
                "status": status.lower(),
                "error_message": error_message,
                "duration": duration_ms,
                "started_at": datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # Send to API
            response = self._post_request("/api/test-cases/", payload)
            
            if response:
                self.api_call_count['api-3'] += 1
                logger.info(f"    ✅ API-3: Test case created - {duration_ms}ms")
            else:
                logger.warning(f"    ⚠️  API-3: Failed to create test case")
            
        except Exception as e:
            logger.error(f"❌ API-3 ERROR: {str(e)}")
            import traceback
            logger.debug(f"    Traceback: {traceback.format_exc()}")
    
    def after_all_tests(self):
        """
        API-4: Update Pipeline Run (After All Tests)
        
        Called once after all tests complete
        Updates pipeline run with final statistics
        """
        if not self.is_jenkins or not self.pipeline_run_id:
            self._print_summary()
            return
        
        try:
            logger.info("")
            logger.info("=" * 63)
            logger.info("📡 API-4: Updating Pipeline Run")
            logger.info("=" * 63)
            
            # Calculate statistics
            total_duration = (time.time() - self.suite_start_time) if self.suite_start_time else 0
            passed_count = sum(1 for t in self.test_results if t['status'] == 'PASSED')
            failed_count = sum(1 for t in self.test_results if t['status'] == 'FAILED')
            skipped_count = sum(1 for t in self.test_results if t['status'] == 'SKIPPED')
            total_count = len(self.test_results)
            
            # Determine overall status
            overall_status = "failed" if failed_count > 0 else "passed"
            
            # Prepare payload
            payload = {
                "status": overall_status,
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "total_tests": total_count,
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "duration": int(total_duration * 1000)  # Convert to milliseconds
            }
            
            # Send to API
            logger.info(f"📤 Request: PATCH /api/pipeline-runs/{self.pipeline_run_id}/")
            success = self._patch_request(f"/api/pipeline-runs/{self.pipeline_run_id}/", payload)
            
            if success:
                self.api_call_count['api-4'] += 1
                logger.info("")
                logger.info("✅ API-4 SUCCESS: Pipeline Run Updated")
                logger.info(f"📊 Total: {total_count} | ✅ {passed_count} | ❌ {failed_count} | ⊘ {skipped_count}")
                logger.info(f"⏱️  Duration: {total_duration:.2f}s ({int(total_duration * 1000)}ms)")
                logger.info(f"🎯 Status: {overall_status.upper()}")
            else:
                logger.error("❌ API-4 ERROR: Failed to update pipeline run")
            
            logger.info("=" * 63)
            logger.info("")
            
            # Print summary
            self._print_api_summary()
            
        except Exception as e:
            logger.error(f"❌ API-4 ERROR: {str(e)}")
            import traceback
            logger.error(f"    Traceback: {traceback.format_exc()}")
    
    def _print_summary(self):
        """Print test execution summary (local runs)"""
        if not self.test_results:
            return
            
        passed = sum(1 for t in self.test_results if t['status'] == 'PASSED')
        failed = sum(1 for t in self.test_results if t['status'] == 'FAILED')
        skipped = sum(1 for t in self.test_results if t['status'] == 'SKIPPED')
        total = len(self.test_results)
        
        logger.info("")
        logger.info("=" * 63)
        logger.info("📊 Test Execution Summary")
        logger.info("=" * 63)
        logger.info(f"Total: {total} | ✅ {passed} | ❌ {failed} | ⊘ {skipped}")
        logger.info("=" * 63)
    
    def _print_api_summary(self):
        """Print API call statistics"""
        logger.info("")
        logger.info("=" * 63)
        logger.info("📡 API Integration Summary")
        logger.info("=" * 63)
        logger.info(f"API-1 (Create Pipeline): {self.api_call_count['api-1']} call(s)")
        logger.info(f"API-3 (Create Test Case): {self.api_call_count['api-3']} call(s)")
        logger.info(f"API-4 (Update Pipeline): {self.api_call_count['api-4']} call(s)")
        logger.info(f"Total API Calls: {sum(self.api_call_count.values())}")
        logger.info("=" * 63)
        logger.info("")
    
    def _post_request(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make POST request to API
        
        Args:
            endpoint: API endpoint (e.g., "/api/pipeline-runs/")
            payload: Request body
            
        Returns:
            Response JSON if successful, None otherwise
        """
        try:
            url = f"{self.api_base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}",
                "ngrok-skip-browser-warning": "true"  # Skip ngrok browser warning
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.warning(f"⚠️  POST {endpoint} returned status: {response.status_code}")
                logger.debug(f"    Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ POST request timeout: {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error: {endpoint}")
            logger.error(f"    Check if API is accessible at: {self.api_base_url}")
            return None
        except Exception as e:
            logger.error(f"❌ POST request failed: {str(e)}")
            return None
    
    def _patch_request(self, endpoint: str, payload: Dict[str, Any]) -> bool:
        """
        Make PATCH request to API
        
        Args:
            endpoint: API endpoint (e.g., "/api/pipeline-runs/{id}/")
            payload: Request body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}",
                "ngrok-skip-browser-warning": "true"
            }
            
            response = requests.patch(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                return True
            else:
                logger.warning(f"⚠️  PATCH {endpoint} returned status: {response.status_code}")
                logger.debug(f"    Response: {response.text}")
                return False
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ PATCH request timeout: {endpoint}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error: {endpoint}")
            return False
        except Exception as e:
            logger.error(f"❌ PATCH request failed: {str(e)}")
            return False


# Global instance - used by conftest.py
api_helper = APIHelper()