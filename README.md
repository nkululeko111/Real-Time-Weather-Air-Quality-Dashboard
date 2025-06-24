# 🌦️ Real-Time Weather & Air Quality Spatial Analysis  
*A Python project that fetches, analyzes, and visualizes spatial weather and air quality data.*  

**Key Features:**  
- Fetches real-time weather (OpenWeatherMap) and air quality (AQICN) data for multiple cities.  
- Exports structured data to CSV/Excel.  
- Generates an interactive **Folium map** with markers for spatial analysis.  
- Demonstrates Python skills (APIs, `pandas`, `folium`).  


## 🛠️ Setup & Installation  
1. **Clone the repository**  
   ```bash
   git clone git@github.com:nkululeko111/Real-Time-Weather-Air-Quality-Dashboard.git
   cd Real-Time-Weather-Air-Quality-Dashboard
   ```

2. **Install dependencies**  
   ```bash
   pip install requests pandas folium openpyxl
   ```

3. **Get API Keys (Free Tier)**  
   - [OpenWeatherMap API](https://openweathermap.org/api)  
   - [AQICN API](https://aqicn.org/api/)  
   - Replace placeholders in `weather_air_quality.py` with your keys:  
     ```python
     OPENWEATHER_API_KEY = "your_api_key_here"
     AQICN_API_KEY = "your_api_key_here"
     ```


## 🚀 How to Run  
```bash
python weather_air_quality.py
```

**Outputs:**  
1. **CSV File**: `weather_aqi_data_TIMESTAMP.csv` (e.g., for Excel analysis).  
2. **Interactive Map**: `weather_aqi_map_TIMESTAMP.html` (open in browser).  


## 📂 Project Structure  
```plaintext
weather-aqi-analysis/
├── weather_air_quality.py  # Main script
├── README.md               # This file
├── weather_aqi_data_*.csv  # Generated data exports
└── weather_aqi_map_*.html  # Generated interactive maps
```


## 📊 Sample Outputs  
### 1. Data Export (CSV)  
| City     | Temperature (°C) | Humidity (%) | AQI | PM2.5 | Latitude | Longitude |  
|----------|------------------|--------------|-----|-------|----------|-----------|  
| London   | 12.5             | 78           | 34  | 12    | 51.5074  | -0.1278   |  

### 2. Interactive Folium Map  
![Folium Map Screenshot](https://i.imgur.com/JQZwzqo.png)  


## 📜 License  
MIT  


**Let me know if you'd like to add:**  
- A "Deployment" section (e.g., hosting the map on GitHub Pages).  
- A "Future Improvements" section (e.g., adding machine learning).  
- Your LinkedIn/GitHub profile links!  

🚀 **Happy coding!**