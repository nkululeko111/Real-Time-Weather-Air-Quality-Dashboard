import requests
import pandas as pd
import folium
from datetime import datetime


class WeatherAQIAnalyzer:
    def __init__(self):
        self.OPENWEATHER_API_KEY = "18f2c990ad65852d30d01f3bdb26f4a6"
        self.AQICN_API_KEY = "2bd011574ea66018f2c6be05dd15c78060686be0"
        self.available_cities = {
            "London": {"lat": 51.5074, "lon": -0.1278},
            "Paris": {"lat": 48.8566, "lon": 2.3522},
            "Berlin": {"lat": 52.5200, "lon": 13.4050},
            "New York": {"lat": 40.7128, "lon": -74.0060},
            "Tokyo": {"lat": 35.6762, "lon": 139.6503},
            "Delhi": {"lat": 28.7041, "lon": 77.1025},
            "Sydney": {"lat": -33.8688, "lon": 151.2093}
        }

    def get_weather_data(self, city):
        """Fetch weather data with comprehensive error handling"""
        if city not in self.available_cities:
            raise ValueError(f"{city} is not in the available cities list")
        
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": self.available_cities[city]["lat"],
                "lon": self.available_cities[city]["lon"],
                "appid": self.OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data.get("main"), dict):
                raise ValueError("Invalid weather data structure")
                
            return {
                "City": city,
                "Temperature (°C)": data["main"]["temp"],
                "Humidity (%)": data["main"]["humidity"],
                "Weather Condition": data["weather"][0]["description"],
                "Latitude": data["coord"]["lat"],
                "Longitude": data["coord"]["lon"],
                "Wind Speed (m/s)": data["wind"]["speed"],
                "Pressure (hPa)": data["main"]["pressure"]
            }
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Weather API connection failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Malformed weather data received: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching weather: {str(e)}")

    def get_air_quality(self, lat, lon):
        """Fetch AQI data with robust error handling"""
        try:
            url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={self.AQICN_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "ok":
                raise ValueError(f"AQI API error: {data.get('data', 'Unknown error')}")
                
            aqi = data["data"]["aqi"]
            pollutants = {
                "PM2.5": data["data"]["iaqi"].get("pm25", {}).get("v", "N/A"),
                "PM10": data["data"]["iaqi"].get("pm10", {}).get("v", "N/A"),
                "O3": data["data"]["iaqi"].get("o3", {}).get("v", "N/A")
            }
            
            return {
                "AQI": aqi,
                **pollutants,
                "AQI Category": self._get_aqi_category(aqi)
            }
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"AQI API connection failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Malformed AQI data received: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching AQI: {str(e)}")

    def _get_aqi_category(self, aqi):
        """Categorize AQI value"""
        if not isinstance(aqi, (int, float)):
            return "N/A"
        if aqi <= 50: return "Good"
        if aqi <= 100: return "Moderate"
        if aqi <= 150: return "Unhealthy for Sensitive Groups"
        if aqi <= 200: return "Unhealthy"
        if aqi <= 300: return "Very Unhealthy"
        return "Hazardous"

    def analyze_cities(self, selected_cities=None):
        """Main analysis function with full error resilience"""
        if not selected_cities:
            selected_cities = list(self.available_cities.keys())
            
        results = []
        failed_cities = []
        
        for city in selected_cities:
            try:
                print(f"\nFetching data for {city}...")
                
                # Get weather data
                weather = self.get_weather_data(city)
                print(f"Weather data fetched: {weather['Temperature (°C)']}°C, {weather['Weather Condition']}")
                
                # Get AQI data
                aqi = self.get_air_quality(weather["Latitude"], weather["Longitude"])
                print(f"AQI data fetched: {aqi['AQI']} ({aqi['AQI Category']})")
                
                # Combine results
                combined = {**weather, **aqi}
                results.append(combined)
                
            except Exception as e:
                print(f"⚠️ Failed to process {city}: {str(e)}")
                failed_cities.append(city)
                continue
        
        if not results:
            raise Exception("All API requests failed. Please check your API keys and internet connection.")
        
        # Create and save DataFrame
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_csv = f"weather_aqi_data_{timestamp}.csv"
        df.to_csv(output_csv, index=False)
        print(f"\n✅ Data saved to {output_csv}")
        
        # Generate map
        try:
            map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
            m = folium.Map(location=map_center, zoom_start=3)
            
            for _, row in df.iterrows():
                popup_text = f"""
                <b>{row['City']}</b><br>
                Temp: {row['Temperature (°C)']}°C<br>
                Weather: {row['Weather Condition']}<br>
                AQI: {row['AQI']} ({row['AQI Category']})<br>
                PM2.5: {row['PM2.5']} µg/m³
                """
                folium.Marker(
                    [row["Latitude"], row["Longitude"]],
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=row["City"],
                    icon=folium.Icon(color=self._get_map_color(row["AQI"]))
                ).add_to(m)
            
            map_file = f"weather_aqi_map_{timestamp}.html"
            m.save(map_file)
            print(f"✅ Map saved to {map_file}")
            
            if failed_cities:
                print(f"\n⚠️ Could not fetch data for: {', '.join(failed_cities)}")
            
            return df, map_file
            
        except Exception as e:
            raise Exception(f"Map generation failed: {str(e)}")

    def _get_map_color(self, aqi):
        """Get marker color based on AQI"""
        try:
            aqi = float(aqi)
            if aqi <= 50: return "green"
            if aqi <= 100: return "blue"
            if aqi <= 150: return "orange"
            if aqi <= 200: return "red"
            if aqi <= 300: return "purple"
            return "black"
        except:
            return "gray"


if __name__ == "__main__":
    analyzer = WeatherAQIAnalyzer()
    
    print("Available cities:", ", ".join(analyzer.available_cities.keys()))
    user_input = input("Enter cities to analyze (comma separated) or press enter for all: ")
    
    selected_cities = [city.strip() for city in user_input.split(",")] if user_input else None
    
    try:
        analyzer.analyze_cities(selected_cities)
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        print("Possible solutions:")
        print("- Check your API keys are valid and activated")
        print("- Verify your internet connection")
        print("- Try again later if API limits are reached")