import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Chart } from 'react-google-charts';
import './App.css';

// Fix Leaflet marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

function App() {
  const [city, setCity] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapCenter, setMapCenter] = useState([51.505, -0.09]); // Default to London coordinates
  const [daysToShow, setDaysToShow] = useState(7);

  const getAQIColor = (aqi) => {
    if (!aqi) return 'gray';
    if (aqi <= 50) return 'green';
    if (aqi <= 100) return 'blue';
    if (aqi <= 150) return 'orange';
    if (aqi <= 200) return 'red';
    if (aqi <= 300) return 'purple';
    return 'black';
  };

  const fetchWeatherData = async () => {
    if (!city.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:5000/api/weather?city=${city}`);
      const [data, status] = await response.json(); // Destructure the array response
      
      if (status !== 200) {
        throw new Error(data.error || 'Failed to fetch weather data');
      }

      console.log("Weather Data:", data); // For debugging
      
      // Validate coordinates before setting state
      if (!data.coordinates || typeof data.coordinates.lat !== 'number' || typeof data.coordinates.lon !== 'number') {
        throw new Error('Invalid coordinates received');
      }

      setWeatherData(data);
      setMapCenter([data.coordinates.lat, data.coordinates.lon]);
      fetchHistoricalData();
    } catch (err) {
      setError(err.message);
      console.error('Error fetching weather:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistoricalData = async () => {
    if (!city.trim()) return;
    
    try {
      const response = await fetch(`http://localhost:5000/api/history?city=${city}&days=${daysToShow}`);
      const [data, status] = await response.json(); // Destructure array response
      
      if (status !== 200) {
        console.error('Historical data error:', data.error);
        return;
      }

      setHistoricalData(data.data || []);
    } catch (err) {
      console.error('Error fetching historical data:', err);
    }
  };

  const exportToCSV = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/export?city=${city}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${city}_weather_data.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        const [errorData] = await response.json();
        setError(errorData.error || 'Export failed');
      }
    } catch (err) {
      setError('Export failed');
      console.error('Export error:', err);
    }
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString();
  };

  const prepareChartData = () => {
    if (!historicalData.length) return [];
    
    const chartData = [
      ['Date', 'Temperature (°C)', 'AQI', 'PM2.5']
    ];
    
    historicalData.forEach(entry => {
      chartData.push([
        new Date(entry.timestamp),
        entry.data.temperature,
        entry.data.aqi,
        entry.data.pm25
      ]);
    });
    
    return chartData;
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🌦️ Weather & Air Quality Monitor</h1>
      </header>
      
      <div className="search-container">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Enter city name"
          onKeyPress={(e) => e.key === 'Enter' && fetchWeatherData()}
        />
        <button onClick={fetchWeatherData} disabled={loading}>
          {loading ? 'Loading...' : 'Search'}
        </button>
        
        <select 
          value={daysToShow} 
          onChange={(e) => setDaysToShow(Number(e.target.value))}
          disabled={!weatherData}
        >
          <option value="1">Last 1 day</option>
          <option value="3">Last 3 days</option>
          <option value="7">Last week</option>
          <option value="30">Last month</option>
        </select>
        
        {weatherData && (
          <button onClick={exportToCSV}>Export to CSV</button>
        )}
      </div>
      
      {error && <div className="error">{error}</div>}
      
      {weatherData && (
        <div className="dashboard">
          <div className="current-weather">
            <h2>Current Conditions in {weatherData.city}</h2>
            <p>Last updated: {formatDate(weatherData.timestamp)}</p>
            
            <div className="weather-cards">
              <div className="weather-card">
                <h3>Temperature</h3>
                <p>{weatherData.temperature} °C</p>
              </div>
              
              <div className="weather-card">
                <h3>Humidity</h3>
                <p>{weatherData.humidity}%</p>
              </div>
              
              <div className="weather-card">
                <h3>Weather</h3>
                <p>{weatherData.weather}</p>
              </div>
              
              <div className="weather-card">
                <h3>Wind Speed</h3>
                <p>{weatherData.wind_speed} m/s</p>
              </div>
              
              <div 
                className="weather-card" 
                style={{ backgroundColor: getAQIColor(weatherData.aqi) }}
              >
                <h3>Air Quality Index</h3>
                <p>{weatherData.aqi || 'N/A'}</p>
                {weatherData.aqi && (
                  <small>{getAQIColor(weatherData.aqi).replace('-', ' ')}</small>
                )}
              </div>
              
              <div className="weather-card">
                <h3>PM2.5</h3>
                <p>{weatherData.pm25 || 'N/A'} µg/m³</p>
              </div>
            </div>
          </div>
          
          <div className="map-container">
            <MapContainer 
              center={mapCenter} 
              zoom={12} 
              style={{ height: '400px', width: '100%' }}
              key={`${mapCenter[0]}-${mapCenter[1]}`} // Force re-render when location changes
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              <Marker position={mapCenter}>
                <Popup>
                  <strong>{weatherData.city}</strong><br />
                  Temp: {weatherData.temperature}°C<br />
                  AQI: {weatherData.aqi || 'N/A'}
                </Popup>
              </Marker>
            </MapContainer>
          </div>
          
          {historicalData.length > 0 && (
            <div className="historical-data">
              <h2>Historical Trends</h2>
              <Chart
                width={'100%'}
                height={'400px'}
                chartType="LineChart"
                loader={<div>Loading Chart</div>}
                data={prepareChartData()}
                options={{
                  title: 'Weather and Air Quality Trends',
                  hAxis: { title: 'Time' },
                  vAxes: [
                    { title: 'Temperature (°C)' },
                    { title: 'AQI / PM2.5', minValue: 0 }
                  ],
                  series: {
                    0: { targetAxisIndex: 0 },
                    1: { targetAxisIndex: 1 },
                    2: { targetAxisIndex: 1 }
                  },
                  legend: { position: 'bottom' }
                }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;