import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Activity, Clock, Layers, Search, ChevronRight, Map as MapIcon } from 'lucide-react';
import './App.css';

const API_URL = '/api/status';

function App() {
  const [data, setData] = useState(null);
  const [selectedCity, setSelectedCity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // v1.1 Detail Panel States
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [selectedRunCard, setSelectedRunCard] = useState(null);
  const POLLING_INTERVAL = 60; // 60s (1 minute) for production
  const [countdown, setCountdown] = useState(POLLING_INTERVAL);
  const [showOnlyFast, setShowOnlyFast] = useState(false);

  const fetchData = async () => {
    try {
      const response = await axios.get(API_URL);
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const nextUpdateRef = React.useRef(Date.now() + POLLING_INTERVAL * 1000);

  useEffect(() => {
    fetchData();
    nextUpdateRef.current = Date.now() + POLLING_INTERVAL * 1000;
    
    const timer = setInterval(() => {
      const remaining = Math.max(0, Math.round((nextUpdateRef.current - Date.now()) / 1000));
      setCountdown(remaining);
      
      if (remaining <= 0) {
        fetchData();
        nextUpdateRef.current = Date.now() + POLLING_INTERVAL * 1000;
      }
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleCustomerClick = async (customerNum, cityCode) => {
    setSelectedCustomer(customerNum);
    setLoadingDetails(true);
    setSelectedRunCard(null); // Reset selection
    try {
      let url = `/api/customer/${encodeURIComponent(customerNum)}`;
      if (cityCode) {
        url += `?city_code=${encodeURIComponent(cityCode)}`;
      }
      const response = await axios.get(url);
      setCustomerDetails(response.data);
      
      // Auto-select the first run_card available
      if (Array.isArray(response.data) && response.data.length > 0) {
        const firstRow = response.data[0];
        const identifier = firstRow.run_card || firstRow.station_code || '紀錄 1';
        setSelectedRunCard(identifier);
      }
    } catch (error) {
      console.error("Error fetching customer details:", error);
      setCustomerDetails([]);
    } finally {
      setLoadingDetails(false);
    }
  };

  const filteredCities = useMemo(() => {
    if (!data) return [];
    
    const lowerSearch = searchTerm ? searchTerm.toLowerCase() : '';
    
    return data.cities.map(city => {
      // Map and filter stations
      const filteredStations = city.stations.map(station => {
        // Map and filter customer stats
        const filteredCustomerStats = (station.customer_stats || []).map(c => {
          // If showOnlyFast is true, filter the run cards
          const rcDetail = c.run_cards_detail || [];
          const matchedRc = showOnlyFast 
            ? rcDetail.filter(rc => rc.fast_level !== '')
            : rcDetail;
            
          if (matchedRc.length === 0) return null;
          
          // Calculate new totals for this customer
          const runCardCount = matchedRc.length;
          const wpnlQty = matchedRc.reduce((sum, rc) => sum + rc.wpnl_qty, 0);
          
          // Max stay time among these run cards
          let maxStay = 0;
          let maxStayRc = '';
          matchedRc.forEach(rc => {
            if (rc.stay_time > maxStay) {
              maxStay = rc.stay_time;
              maxStayRc = rc.run_card;
            }
          });
          
          // Determine highest fast level for this customer at this station
          let highestLevel = '';
          if (matchedRc.some(rc => rc.fast_level === 'A')) highestLevel = 'A';
          else if (matchedRc.some(rc => rc.fast_level === 'B')) highestLevel = 'B';
          else if (matchedRc.some(rc => rc.fast_level === 'C')) highestLevel = 'C';
          else if (matchedRc.some(rc => rc.fast_level === 'D')) highestLevel = 'D';
          
          return {
            ...c,
            run_card_count: runCardCount,
            wpnl_qty: wpnlQty,
            max_stay_time: maxStay,
            max_stay_run_card: maxStayRc,
            highest_fast_level: highestLevel,
            run_cards_detail: matchedRc
          };
        }).filter(Boolean);
        
        // Filter customer stats by search term
        const searchFilteredStats = filteredCustomerStats.filter(c => {
          const lowerSearchTerm = lowerSearch.toLowerCase();
          const matchEng = c.eng_num.toLowerCase().includes(lowerSearchTerm);
          const matchCat = c.category && c.category.toLowerCase().includes(lowerSearchTerm);
          return !lowerSearch || matchEng || matchCat;
        });
        
        if (searchFilteredStats.length === 0) return null;
        
        return {
          ...station,
          customers: searchFilteredStats.map(c => c.eng_num),
          customer_stats: searchFilteredStats,
          count: searchFilteredStats.reduce((sum, c) => sum + c.run_card_count, 0)
        };
      }).filter(Boolean);
      
      // Calculate city stats based on filteredStations
      const cityStats = filteredStations.reduce((acc, station) => {
        acc.customers += station.customer_stats.length;
        acc.wip += station.count;
        acc.wpnl += station.customer_stats.reduce((sum, c) => sum + c.wpnl_qty, 0);
        acc.stations += 1;
        return acc;
      }, { customers: 0, wip: 0, wpnl: 0, stations: 0 });
      
      return {
        ...city,
        stations: filteredStations,
        cityStats
      };
    }).filter(city => city.stations.length > 0);
  }, [data, searchTerm, showOnlyFast]);

  const currentSelectedCity = useMemo(() => {
    if (!selectedCity) return null;
    return filteredCities.find(c => c.city_code === selectedCity.city_code) || null;
  }, [filteredCities, selectedCity]);

  const getFastLevel = (typeStr) => {
    if (!typeStr) return '';
    const str = String(typeStr);
    if (str.includes('A')) return 'A';
    if (str.includes('B')) return 'B';
    if (str.includes('C')) return 'C';
    if (str.includes('D')) return 'D';
    return '';
  };

  const createClusterIcon = (count, code, isMainline) => {
    return L.divIcon({
      html: `<div class="cluster-marker ${isMainline ? 'mainline' : 'special'}" translate="no">
               <span class="city-code">${code}</span>
               <span class="count">${count}</span>
             </div>`,
      className: 'custom-cluster',
      iconSize: L.point(55, 55),
    });
  };

  if (loading || !data) {
    return <div className="loading">載入 WIP 數據中...</div>;
  }

  const flowPath = filteredCities
    .filter(c => c.is_mainline)
    .sort((a, b) => a.order - b.order)
    .map(c => [c.lat, c.lng]);

  return (
    <div className="app-container" translate="no">
      <aside className="sidebar">
        <header>
          <div className="logo">
            <Layers className="icon" />
            <h1>WIP Status (v1.9)</h1>
          </div>
          <p className="update-time">
            <Clock size={14} /> Last Sync: {data.last_update}
          </p>
          <p className="countdown-display" style={{fontSize: '0.8rem', color: '#22d3ee', marginTop: '0.25rem', fontWeight: 'bold'}}>
            ⏱️ Next update in: {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
          </p>
          <p className="file-name-display" style={{fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
            📄 {data.file_name}
          </p>

          {/* Fast Order Filter Toggle */}
          <div className="filter-section" style={{
            marginTop: '1rem',
            padding: '0.6rem 0.8rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#22d3ee', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              ⚡ 只顯示急單/快單
            </span>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={showOnlyFast} 
                onChange={(e) => setShowOnlyFast(e.target.checked)} 
              />
              <span className="slider round"></span>
            </label>
          </div>
        </header>

        <div className="city-list">
          {filteredCities.length > 0 ? (
            filteredCities.map(city => (
              <div 
                key={city.city_code} 
                className={`city-item ${currentSelectedCity?.city_code === city.city_code ? 'active' : ''}`}
                onClick={() => setSelectedCity(city)}
              >
                <div className="city-info">
                  <h3 translate="no">{city.city_code}</h3>
                  <p>{city.cityStats.stations} STATIONS | {city.cityStats.wip} WIP | {city.cityStats.wpnl} WPNL</p>
                </div>
                <ChevronRight size={20} />
              </div>
            ))
          ) : (
            <div style={{padding: '2rem', textAlign: 'center', color: '#94a3b8'}}>
              查無此客戶的在製品資料
            </div>
          )}
        </div>
      </aside>

      <main className="map-area">
        <div className="floating-search">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="搜尋客戶編號 (例如: eng_num)..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button onClick={() => setSearchTerm('')} className="clear-btn">&times;</button>
          )}
        </div>

        <MapContainer 
          center={[23.8, 121.0]} 
          zoom={8} 
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
            attribution='&copy; CARTO'
          />
          
          <Polyline 
            positions={flowPath} 
            pathOptions={{ color: '#22d3ee', weight: 2, dashArray: '5, 10', opacity: 0.4 }} 
          />

          {filteredCities.map(city => (
            <Marker 
              key={city.city_code} 
              position={[city.lat, city.lng]}
              icon={createClusterIcon(city.cityStats.wip, city.city_code, city.is_mainline)}
              eventHandlers={{
                click: () => setSelectedCity(city),
              }}
            >
              <Popup className="custom-popup">
                <div className="popup-content" translate="no">
                  <h2 style={{color: '#22d3ee'}}>{city.city_code}</h2>
                  <div className="station-details">
                    {city.stations.map(s => {
                      const lowerSearchTerm = searchTerm.toLowerCase();
                      const hasSearchedCustomer = !searchTerm || s.customers.some(c => {
                        const matchEng = c.toString().toLowerCase().includes(lowerSearchTerm);
                        const stats = s.customer_stats || [];
                        const matchCat = stats.some(stat => stat.eng_num === c && stat.category && stat.category.toLowerCase().includes(lowerSearchTerm));
                        return matchEng || matchCat;
                      });
                      if (!hasSearchedCustomer) return null;

                      return (
                        <div key={s.station_code} className="station-row">
                          <span style={{fontWeight: 'bold'}}>{s.station_code}:</span>
                          <span style={{color: '#22d3ee'}}>{s.count} Items</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
          <MapController selectedCity={currentSelectedCity} />
        </MapContainer>
        
        {currentSelectedCity && (
          <div className="detail-overlay glass">
            <button className="close-btn" onClick={() => setSelectedCity(null)}>&times;</button>
            <h2 translate="no">{currentSelectedCity.city_code} WIP Details</h2>
            <div className="stations-grid">
              {currentSelectedCity.stations.map(s => {
                // Backward compatibility if customer_stats is not ready yet
                const stats = s.customer_stats || s.customers.map(c => ({ eng_num: c, run_card_count: 1, wpnl_qty: 0, max_stay_time: 0, max_stay_run_card: '' }));
                const filteredStats = stats.filter(c => {
                  const lowerSearchTerm = searchTerm.toLowerCase();
                  const matchEng = c.eng_num.toLowerCase().includes(lowerSearchTerm);
                  const matchCat = c.category && c.category.toLowerCase().includes(lowerSearchTerm);
                  return !searchTerm || matchEng || matchCat;
                });
                if (searchTerm && filteredStats.length === 0) return null;

                const totalRunCards = filteredStats.reduce((sum, c) => sum + c.run_card_count, 0);
                const totalWpnl = filteredStats.reduce((sum, c) => sum + c.wpnl_qty, 0);

                let maxStayTime = 0;
                let maxStayRunCard = '';
                let maxStayEngNum = '';
                filteredStats.forEach(c => {
                  if (c.max_stay_time > maxStayTime) {
                    maxStayTime = c.max_stay_time;
                    maxStayRunCard = c.max_stay_run_card;
                    maxStayEngNum = c.eng_num;
                  }
                });

                return (
                  <div key={s.station_code} className="station-card">
                    <h4>{s.station_code}</h4>
                    <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem'}}>
                      <p className="count-badge">{filteredStats.length} Customers</p>
                      <p className="count-badge" style={{backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa'}}>{totalRunCards} Run Cards</p>
                      <p className="count-badge" style={{backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399'}}>{totalWpnl} WPNL</p>
                      {maxStayTime > 0 && (
                        <p className="count-badge" style={{backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171'}}>最長停留: {maxStayTime}H ({maxStayRunCard} / {maxStayEngNum})</p>
                      )}
                    </div>
                    <div className="customer-list">
                      {filteredStats.map(c => (
                        <span 
                          key={c.eng_num} 
                          className={`customer-tag ${searchTerm ? 'highlight' : ''} ${c.highest_fast_level ? `fast-blink-${c.highest_fast_level}` : ''}`} 
                          translate="no"
                          onClick={() => handleCustomerClick(c.eng_num, currentSelectedCity.city_code)}
                        >
                          {c.eng_num}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>

      {/* v1.1 Right Side Detail Panel */}
      <div className={`customer-detail-panel ${selectedCustomer ? 'open' : ''}`}>
        <div className="header">
          <h2>客戶詳細資料</h2>
          <button className="close-panel-btn" onClick={() => setSelectedCustomer(null)}>&times;</button>
        </div>
        
        {loadingDetails ? (
          <div className="loading-text">向資料庫查詢中...</div>
        ) : Array.isArray(customerDetails) && customerDetails.length > 0 ? (
          <div className="content-wrapper">
            {/* Run Card Tabs */}
            <div className="run-card-tabs">
              <h4>選擇 Run Card (批號):</h4>
              <div className="tabs-container">
                {customerDetails.map((row, idx) => {
                  const identifier = row.run_card || row.station_code || `紀錄 ${idx + 1}`;
                  const fastLevel = getFastLevel(row['是否快單']);
                  return (
                    <button 
                      key={idx}
                      className={`run-card-tab ${selectedRunCard === identifier ? 'active' : ''} ${fastLevel ? `fast-tab-blink-${fastLevel}` : ''}`}
                      onClick={() => setSelectedRunCard(identifier)}
                    >
                      {identifier}
                      {fastLevel && <span className="fast-badge">{fastLevel}</span>}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Detail Content Table */}
            <div className="content">
              {customerDetails.map((row, index) => {
                const identifier = row.run_card || row.station_code || `紀錄 ${index + 1}`;
                
                // Only render the table for the selected run_card
                if (identifier !== selectedRunCard) return null;

                const fastLevel = getFastLevel(row['是否快單']);

                return (
                  <div key={index} className={`detail-row-card ${fastLevel ? `fast-card-${fastLevel}` : ''}`}>
                    <div className="detail-row-card-header">
                      <span>{row['eng_num'] || selectedCustomer}</span>
                      <span style={{fontSize: '0.8rem', opacity: 0.8}}>
                        {fastLevel && <span style={{marginRight: '0.5rem', background: 'rgba(255,255,255,0.2)', padding: '0.1rem 0.4rem', borderRadius: '4px'}}>快單 {fastLevel}</span>}
                        {identifier}
                      </span>
                    </div>
                    <table className="detail-table">
                      <tbody>
                        {Object.entries(row).map(([key, value]) => {
                          if (key === 'eng_num_str' || key === 'city_code') return null;
                          return (
                            <tr key={key}>
                              <th>{key}</th>
                              <td>{value !== null && value !== '' ? String(value) : '-'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="content">
            <div className="no-results">找不到該客戶的詳細資料</div>
          </div>
        )}
      </div>

    </div>
  );
}

function MapController({ selectedCity }) {
  const map = useMap();
  useEffect(() => {
    if (selectedCity) {
      map.flyTo([selectedCity.lat, selectedCity.lng], 11);
    }
  }, [selectedCity, map]);
  return null;
}

export default App;
