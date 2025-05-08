from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Profile, APIEndpoint, Server, TestRun, TestResult
import json
import requests
import csv
import io
import re
import time
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Rate limiting settings
RATE_LIMIT_DELAY = 1  # seconds between requests
MAX_CONCURRENT_REQUESTS = 3  # maximum number of concurrent requests
RATE_LIMIT_KEY_PREFIX = 'rate_limit_'

def index(request):
    profiles = Profile.objects.all()
    api_endpoints = APIEndpoint.objects.all()
    servers = Server.objects.filter(is_active=True)
    return render(request, 'api_tester/index.html', {
        'profiles': profiles,
        'api_endpoints': api_endpoints,
        'servers': servers
    })

def profile_detail(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    # Get all profiles for the target profile dropdown
    all_profiles = Profile.objects.all()
    api_endpoints = APIEndpoint.objects.all()
    servers = Server.objects.filter(is_active=True)
    return render(request, 'api_tester/profile_detail.html', {
        'profile': profile,
        'profiles': all_profiles,
        'api_endpoints': api_endpoints,
        'servers': servers
    })


def create_profile(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        # Process cookies from key/value pairs
        cookie_keys = request.POST.getlist('cookie_key[]')
        cookie_values = request.POST.getlist('cookie_value[]')
        cookies = {}
        for key, value in zip(cookie_keys, cookie_values):
            if key and value:  # Only add if both key and value are provided
                cookies[key] = value
        
        # Process parameters from key/value pairs
        param_keys = request.POST.getlist('param_key[]')
        param_values = request.POST.getlist('param_value[]')
        common_parameters = {}
        for key, value in zip(param_keys, param_values):
            if key and value:  # Only add if both key and value are provided
                common_parameters[key] = value
        
        profile = Profile.objects.create(
            name=name,
            description=description,
            cookies=cookies,
            common_parameters=common_parameters
        )
        
        messages.success(request, 'Profile created successfully!')
        return redirect('profiles')
    
    return render(request, 'api_tester/create_profile.html')

def servers(request):
    servers = Server.objects.all()
    return render(request, 'api_tester/servers.html', {
        'servers': servers
    })

@csrf_exempt
def server_detail(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    if request.method == 'GET':
        return JsonResponse({
            'id': server.id,
            'name': server.name,
            'base_url': server.base_url,
            'description': server.description,
            'is_active': server.is_active
        })
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            server.name = data.get('name', server.name)
            server.base_url = data.get('base_url', server.base_url)
            server.description = data.get('description', server.description)
            server.full_clean()  # Validate the model
            server.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def create_server(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            server = Server.objects.create(
                name=data['name'],
                base_url=data['base_url'],
                description=data.get('description', '')
            )
            return JsonResponse({
                'id': server.id,
                'name': server.name,
                'base_url': server.base_url,
                'description': server.description,
                'is_active': server.is_active
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def toggle_server_status(request, server_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            server = get_object_or_404(Server, id=server_id)
            server.is_active = data.get('is_active', not server.is_active)
            server.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def test_endpoint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile_id = data.get('profile_id')
            endpoint_id = data.get('endpoint_id')
            server_id = data.get('server_id')
            target_profile_id = data.get('target_profile_id')
            parameters = data.get('parameters', {})
            test_run_id = data.get('test_run_id')
            
            # Get rate limit parameters from request or use defaults
            rate_limit_delay = float(data.get('rate_limit_delay', RATE_LIMIT_DELAY))
            max_concurrent_requests = int(data.get('max_concurrent_requests', MAX_CONCURRENT_REQUESTS))

            if not profile_id:
                return JsonResponse({'error': 'Profile ID is required'}, status=400)
            if not endpoint_id:
                return JsonResponse({'error': 'Endpoint ID is required'}, status=400)
            if not server_id:
                return JsonResponse({'error': 'Server ID is required'}, status=400)

            # Check rate limit
            server_key = f"{RATE_LIMIT_KEY_PREFIX}{server_id}"
            current_requests = cache.get(server_key, 0)
            
            if current_requests >= max_concurrent_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'retry_after': rate_limit_delay
                }, status=429)
            
            # Increment request counter
            cache.set(server_key, current_requests + 1, timeout=60)
            
            try:
                profile = Profile.objects.get(id=profile_id)
                endpoint = APIEndpoint.objects.get(id=endpoint_id)
                server = Server.objects.get(id=server_id)
                
                # Create or get test run
                if not test_run_id:
                    test_run = TestRun.objects.create(
                        profile=profile,
                        server=server,
                        target_profile_id=target_profile_id,
                        status='in_progress'
                    )
                else:
                    test_run = TestRun.objects.get(id=test_run_id)
                
                results = []
                
                # Function to run a single test
                def run_test(use_target_params=False):
                    # Add delay between requests
                    time.sleep(rate_limit_delay)
                    
                    # Merge profile cookies and parameters
                    cookies = profile.cookies
                    all_parameters = {**profile.common_parameters, **parameters}
                    
                    # If using target profile parameters, merge them
                    if use_target_params and target_profile_id:
                        target_profile = Profile.objects.get(id=target_profile_id)
                        all_parameters = {**target_profile.common_parameters, **parameters}
                    
                    # Construct the full URL
                    base_url = server.base_url.rstrip('/')
                    endpoint_path = endpoint.endpoint.strip('/')
                    
                    # Replace path parameters with values from all_parameters
                    path_params = re.findall(r'{([^}]+)}', endpoint_path)
                    for param in path_params:
                        if param in all_parameters:
                            endpoint_path = endpoint_path.replace(f'{{{param}}}', str(all_parameters[param]))
                            all_parameters.pop(param)
                    
                    full_url = f"{base_url}/{endpoint_path}"
                    
                    try:
                        response = requests.request(
                            method=endpoint.method,
                            url=full_url,
                            cookies=cookies,
                            params=all_parameters if endpoint.method == 'GET' else None,
                            json=all_parameters if endpoint.method != 'GET' else None
                        )
                        
                        # Save successful result
                        test_result = TestResult.objects.create(
                            test_run=test_run,
                            endpoint=endpoint,
                            request_url=full_url,
                            request_method=endpoint.method,
                            request_parameters=all_parameters,
                            response_status=response.status_code,
                            response_headers=dict(response.headers),
                            response_data=response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                            test_type='target_params' if use_target_params else 'normal'
                        )
                        
                        return {
                            'status': response.status_code,
                            'headers': dict(response.headers),
                            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                            'test_result_id': test_result.id
                        }
                        
                    except Exception as e:
                        # Save failed result
                        test_result = TestResult.objects.create(
                            test_run=test_run,
                            endpoint=endpoint,
                            request_url=full_url,
                            request_method=endpoint.method,
                            request_parameters=all_parameters,
                            response_status=0,
                            error_message=str(e),
                            test_type='target_params' if use_target_params else 'normal'
                        )
                        raise e
                
                # Run normal test
                try:
                    normal_result = run_test(use_target_params=False)
                    results.append(normal_result)
                except Exception as e:
                    results.append({'error': str(e)})
                    test_run.status = 'failed'
                    test_run.save()
                    return JsonResponse({'error': str(e)}, status=500)
                
                # Run target profile test if target profile is specified
                if target_profile_id:
                    try:
                        target_result = run_test(use_target_params=True)
                        results.append(target_result)
                    except Exception as e:
                        results.append({'error': str(e)})
                        test_run.status = 'failed'
                        test_run.save()
                        return JsonResponse({'error': str(e)}, status=500)
                
                # Update test run status
                test_run.status = 'completed'
                test_run.save()
                
                return JsonResponse({
                    'results': results,
                    'test_run_id': test_run.id
                })
                
            finally:
                # Decrement request counter
                current_requests = cache.get(server_key, 0)
                if current_requests > 0:
                    cache.set(server_key, current_requests - 1, timeout=60)
            
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found'}, status=404)
        except APIEndpoint.DoesNotExist:
            return JsonResponse({'error': 'Endpoint not found'}, status=404)
        except Server.DoesNotExist:
            return JsonResponse({'error': 'Server not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in parameters'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def test_runs(request):
    test_runs = TestRun.objects.all().order_by('-created_at')
    return render(request, 'api_tester/test_runs.html', {
        'test_runs': test_runs
    })

def test_run_detail(request, test_run_id):
    test_run = get_object_or_404(TestRun, id=test_run_id)
    results = test_run.results.all()
    return render(request, 'api_tester/test_run_detail.html', {
        'test_run': test_run,
        'results': results
    })

@csrf_exempt
def import_api_endpoints(request):
    if request.method == 'POST':
        try:
            # Handle CSV file upload
            if 'csv_file' in request.FILES:
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(decoded_file))
                
                for row in csv_reader:
                    APIEndpoint.objects.create(
                        name=row['name'],
                        method=row['method'],
                        endpoint=row['endpoint'],
                        description=row.get('description', ''),
                        required_parameters=json.loads(row.get('required_parameters', '[]'))
                    )
                
                messages.success(request, 'Endpoints imported successfully from CSV')
                return redirect('index')
            
            # Handle JSON data
            elif 'json_data' in request.POST:
                json_data = json.loads(request.POST['json_data'])
                for endpoint_data in json_data:
                    APIEndpoint.objects.create(
                        name=endpoint_data['name'],
                        method=endpoint_data['method'],
                        endpoint=endpoint_data['endpoint'],
                        description=endpoint_data.get('description', ''),
                        required_parameters=endpoint_data.get('required_parameters', [])
                    )
                
                messages.success(request, 'Endpoints imported successfully from JSON')
                return redirect('index')
            
            # Handle plain text
            elif 'plain_text' in request.POST:
                text_data = request.POST['plain_text'].strip()
                lines = text_data.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to extract method and endpoint
                    method_match = re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+(.+)$', line)
                    if method_match:
                        method = method_match.group(1)
                        endpoint = method_match.group(2)
                    else:
                        # Auto-detect method based on endpoint pattern
                        endpoint = line
                        if re.search(r'/\d+$', endpoint) or re.search(r'/[a-zA-Z0-9-]+$', endpoint):
                            method = 'GET'
                        elif re.search(r'/create$', endpoint) or re.search(r'/new$', endpoint):
                            method = 'POST'
                        elif re.search(r'/update$', endpoint) or re.search(r'/edit$', endpoint):
                            method = 'PUT'
                        elif re.search(r'/delete$', endpoint) or re.search(r'/remove$', endpoint):
                            method = 'DELETE'
                        else:
                            method = 'GET'
                    
                    # Extract name from endpoint
                    name = endpoint.split('/')[-1].replace('-', ' ').title()
                    
                    # Extract required parameters from path variables
                    required_params = []
                    path_params = re.findall(r'{([^}]+)}', endpoint)
                    required_params.extend(path_params)
                    
                    APIEndpoint.objects.create(
                        name=name,
                        method=method,
                        endpoint=endpoint,
                        required_parameters=required_params
                    )
                
                messages.success(request, 'Endpoints imported successfully from plain text')
                return redirect('index')
            
            return JsonResponse({'error': 'No valid import data provided'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return render(request, 'api_tester/import_api_endpoints.html')

@csrf_exempt
def edit_profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    if request.method == 'POST':
        try:
            profile.name = request.POST.get('name')
            profile.description = request.POST.get('description', '')
            
            # Process cookies from key-value pairs
            cookies = {}
            cookie_keys = request.POST.getlist('cookie_key[]')
            cookie_values = request.POST.getlist('cookie_value[]')
            for key, value in zip(cookie_keys, cookie_values):
                if key and value:  # Only add non-empty pairs
                    cookies[key] = value
            
            # Process common parameters from key-value pairs
            common_parameters = {}
            param_keys = request.POST.getlist('param_key[]')
            param_values = request.POST.getlist('param_value[]')
            for key, value in zip(param_keys, param_values):
                if key and value:  # Only add non-empty pairs
                    common_parameters[key] = value
            
            profile.cookies = cookies
            profile.common_parameters = common_parameters
            profile.save()
            
            messages.success(request, 'Profile updated successfully')
            return redirect('profile_detail', profile_id=profile.id)
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'api_tester/edit_profile.html', {
        'profile': profile
    })

def profiles(request):
    profiles = Profile.objects.all()
    return render(request, 'api_tester/profiles.html', {
        'profiles': profiles
    })

def endpoints(request):
    api_endpoints = APIEndpoint.objects.all()
    return render(request, 'api_tester/endpoints.html', {
        'api_endpoints': api_endpoints
    })

def test_endpoints(request):
    profiles = Profile.objects.all()
    servers = Server.objects.all()
    endpoints = APIEndpoint.objects.all()
    
    context = {
        'profiles': profiles,
        'servers': servers,
        'endpoints': endpoints,
    }
    return render(request, 'api_tester/test_endpoints.html', context)

def test_result_detail(request, result_id):
    result = get_object_or_404(TestResult, id=result_id)
    return render(request, 'api_tester/test_result_detail.html', {
        'result': result
    })
