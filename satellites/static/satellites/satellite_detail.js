(function(){
  function renderSatelliteMap(target, options){
    if(!window.L){
      console.warn("Leaflet library not loaded; map cannot be rendered.");
      return;
    }

    const { lat, lon, label } = options;
    if(typeof lat !== "number" || typeof lon !== "number"){
      console.warn("Invalid lat/lon provided for satellite map.");
      return;
    }

    const map = L.map(target, {
      zoomControl: true,
      attributionControl: false,
    }).setView([lat, lon], 3);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 8,
      minZoom: 2,
      crossOrigin: true,
    }).addTo(map);

    const marker = L.marker([lat, lon], {
      title: label || "Satellite position",
    }).addTo(map);

    marker.bindTooltip(label || "Satellite position", { permanent: true, direction: "top" });

    const bounds = marker.getLatLng().toBounds(4000000); // approx range for context
    map.fitBounds(bounds, { maxZoom: 5 });

    return map;
  }

  window.StarlightMap = {
    renderSatelliteMap,
  };

  document.addEventListener("DOMContentLoaded", function(){
    const container = document.getElementById("satellite-map");
    if(!container){
      return;
    }

    const lat = parseFloat(container.dataset.lat);
    const lon = parseFloat(container.dataset.lon);
    const label = container.dataset.label;

    if(!Number.isFinite(lat) || !Number.isFinite(lon)){
      return;
    }

    const map = renderSatelliteMap(container, { lat, lon, label });
    if(!map){
      return;
    }
  });
})();
