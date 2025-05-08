# Permitter - API Testing Tool

Permitter is a powerful API testing tool that allows you to create profiles with cookies and common parameters, then test API endpoints against different servers. It's perfect for testing APIs that require authentication or specific parameters.

## Features

- **Profile Management**
  - Create and manage testing profiles
  - Store cookies and common parameters per profile
  - Use profiles as templates for API testing

- **Server Management**
  - Add multiple server environments
  - Toggle servers on/off
  - Test against different environments easily

- **API Endpoint Testing**
  - Import endpoints from CSV, JSON, or plain text
  - Test endpoints with profile configurations
  - View detailed test results
  - Rate limiting to prevent server overload
  - Search and filter endpoints
  - Select/deselect multiple endpoints

- **Test Results**
  - View test run history
  - Detailed response information
  - Compare results between profiles
  - Export test results

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/permitter.git
   cd permitter
   ```

2. Build and run with Docker:
   ```bash
   docker compose up --build
   ```

3. Access the application at http://localhost:8000

### Manual Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

1. **Create a Profile**
   - Go to Profiles page
   - Click "New Profile"
   - Add cookies and common parameters
   - Save the profile

2. **Add Servers**
   - Go to Servers page
   - Add your API servers
   - Toggle servers on/off as needed

3. **Import Endpoints**
   - Go to Endpoints page
   - Import endpoints from CSV, JSON, or plain text
   - Or add endpoints manually

4. **Run Tests**
   - Go to Test Endpoints page
   - Select a profile and server
   - Choose endpoints to test
   - Configure rate limiting if needed
   - Run the tests

5. **View Results**
   - Check test run history
   - View detailed results
   - Compare responses

## Rate Limiting

The application includes configurable rate limiting to prevent overwhelming your APIs:

- **Delay Between Requests**: Set the time to wait between requests
- **Max Concurrent Requests**: Limit the number of simultaneous requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Django
- Uses Tailwind CSS for styling
- Inspired by the need for better API testing tools 