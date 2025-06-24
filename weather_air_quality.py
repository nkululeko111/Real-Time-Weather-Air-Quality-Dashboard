import requests
import pandas as pd
import folium
from datetime import datetime

# API Keys (replace with yours)
OPENWEATHER_API_KEY = "18f2c990ad65852d30d01f3bdb26f4a6"
AQICN_API_KEY = "2bd011574ea66018f2c6be05dd15c78060686be0"

# Fetch Weather Data (OpenWeatherMap)
def get_weather_data(city="London"):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    return {
        "City": city,
        "Temperature (°C)": data["main"]["temp"],
        "Humidity (%)": data["main"]["humidity"],
        "Weather": data["weather"][0]["description"],
        "Latitude": data["coord"]["lat"],
        "Longitude": data["coord"]["lon"]
    }

# Fetch Air Quality Data (AQICN)
def get_air_quality(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return {
        "AQI": data["data"]["aqi"],
        "PM2.5": data["data"]["iaqi"]["pm25"]["v"] if "pm25" in data["data"]["iaqi"] else "N/A"
    }

# Main Script
if __name__ == "__main__":
    # Cities to analyze
    cities = ["London", "Paris", "Berlin", "New York", "Tokyo"]

    # Fetch data for each city
    results = []
    for city in cities:
        try:
            weather = get_weather_data(city)
            aqi = get_air_quality(weather["Latitude"], weather["Longitude"])
            combined = {**weather, **aqi}
            results.append(combined)
        except Exception as e:
            print(f"Error fetching data for {city}: {e}")

    # Create DataFrame
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_csv = f"weather_aqi_data_{timestamp}.csv"
    df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")

    # Generate Interactive Map
    map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
    m = folium.Map(location=map_center, zoom_start=4)

    for _, row in df.iterrows():
        popup_text = f"""
        City: {row['City']}<br>
        Temp: {row['Temperature (°C)']}°C<br>
        AQI: {row['AQI']} (PM2.5: {row['PM2.5']})
        """
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            popup=popup_text,
            tooltip=row["City"]
        ).add_to(m)

    map_file = f"weather_aqi_map_{timestamp}.html"
    m.save(map_file)
    print(f"Map saved to {map_file}. Open in a browser.")