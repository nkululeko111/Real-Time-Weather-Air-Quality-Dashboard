import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from functools import lru_cache
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'data_exports'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class WeatherAQIService:
    def __init__(self):
        self.OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
        self.AQICN_API_KEY = os.getenv('AQICN_API_KEY')
        self.cache_duration = timedelta(minutes=30)
        self.historical_data = self._load_historical_data()
        
        if not self.OPENWEATHER_API_KEY or not self.AQICN_API_KEY:
            raise EnvironmentError("Missing API keys! Please set them in your .env file.")

    def _load_historical_data(self):
        try:
            with open('historical_data.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_historical_data(self):
        with open('historical_data.json', 'w') as f:
            json.dump(self.historical_data, f)

    def _normalize_city_name(self, city):
        """Capitalize first letter, lowercase the rest, handle edge cases"""
        if not city:
            return None
        city = city.strip()
        # Handle special cases like "New York"
        special_cases = {
            'new york': 'New York',
            'los angeles': 'Los Angeles',
            'rio de janeiro': 'Rio de Janeiro'
        }
        return special_cases.get(city.lower(), city.title())

    @lru_cache(maxsize=100)
    def _get_coordinates(self, city):
        """Get coordinates with better error handling and retries"""
        try:
            # First try direct geocoding
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={self.OPENWEATHER_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                return {'lat': data[0]['lat'], 'lon': data[0]['lon']}
            
            # If direct fails, try fuzzy search
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={city.lower()}&limit=5&appid={self.OPENWEATHER_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data and isinstance(data, list):
                for location in data:
                    if city.lower() in location.get('name', '').lower():
                        return {'lat': location['lat'], 'lon': location['lon']}
            
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error during coordinate lookup: {str(e)}")
            return None
        except KeyError as e:
            print(f"Key error during coordinate lookup: {str(e)}")
            return None
        except ValueError as e:
            print(f"Value error during coordinate lookup: {str(e)}")
            return None    

    def get_weather_data(self, city):
        """Fetch current weather with timestamp"""
        normalized_city = self._normalize_city_name(city)
        if not normalized_city:
            return {'error': 'Invalid city name'}, 400

        try:
            coords = self._get_coordinates(normalized_city)
            if not coords:
                return {'error': 'City not found'}, 404

            # Get weather data
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={self.OPENWEATHER_API_KEY}&units=metric"
            weather_response = requests.get(weather_url, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # Get AQI data
            aqi_url = f"https://api.waqi.info/feed/geo:{coords['lat']};{coords['lon']}/?token={self.AQICN_API_KEY}"
            aqi_response = requests.get(aqi_url, timeout=10)
            aqi_data = aqi_response.json() if aqi_response.status_code == 200 else {}

            # Process data
            current_time = datetime.utcnow()
            processed_data = {
                'city': normalized_city,
                'timestamp': current_time.isoformat(),
                'data_time': weather_data.get('dt', None),
                'temperature': weather_data['main']['temp'],
                'humidity': weather_data['main']['humidity'],
                'weather': weather_data['weather'][0]['description'],
                'wind_speed': weather_data['wind']['speed'],
                'aqi': aqi_data.get('data', {}).get('aqi', None),
                'pm25': aqi_data.get('data', {}).get('iaqi', {}).get('pm25', {}).get('v', None),
                'coordinates': coords
            }

            # Store historical data
            if normalized_city not in self.historical_data:
                self.historical_data[normalized_city] = []
            self.historical_data[normalized_city].append({
                'timestamp': current_time.isoformat(),
                'data': processed_data
            })
            self._save_historical_data()

            return processed_data, 200

        except Exception as e:
            return {'error': str(e)}, 500

    def get_historical_data(self, city, days=7):
        """Get historical data for a city"""
        normalized_city = self._normalize_city_name(city)
        if not normalized_city:
            return {'error': 'Invalid city name'}, 400

        if normalized_city not in self.historical_data:
            return {'error': 'No historical data available'}, 404

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        historical = [
            entry for entry in self.historical_data[normalized_city]
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
        ]
        return {'city': normalized_city, 'data': historical}, 200

    def export_to_csv(self, city):
        """Export data to CSV"""
        normalized_city = self._normalize_city_name(city)
        if not normalized_city:
            return {'error': 'Invalid city name'}, 400

        if normalized_city not in self.historical_data:
            return {'error': 'No data available'}, 404

        df = pd.DataFrame([entry['data'] for entry in self.historical_data[normalized_city]])
        filename = f"{secure_filename(normalized_city)}_weather_data_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(filepath, index=False)
        return filepath, 200

# Initialize the service
service = WeatherAQIService()

@app.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    return jsonify(*service.get_weather_data(city))

@app.route('/api/history', methods=['GET'])
def get_history():
    city = request.args.get('city')
    days = int(request.args.get('days', 7))
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    return jsonify(*service.get_historical_data(city, days))

@app.route('/api/export', methods=['GET'])
def export_data():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    filepath, status = service.export_to_csv(city)
    if status != 200:
        return jsonify({'error': filepath}), status
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)