async function configure() {
    const request = new Request("./variables.json");
    const response = await fetch(request);
    const variables = await response.json();
    new WrapperWS(variables.url);
}

function popupText(aircraft) {
    return `<b>${aircraft.number}</b>&nbsp;${aircraft.origin}&rarr;${aircraft.destination}`
}

function WrapperWS(url) {
    var flyingIcon = L.icon({
        iconUrl: 'img/green.svg',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    });
    var landedIcon = L.icon({
        iconUrl: 'img/orange.svg',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    });

    if ("WebSocket" in window) {
        var ws = new WebSocket(url);

        ws.onopen = function (evt) {
            ws.send("hello!")
            console.log("Waiting for the configuration...", evt);
        };

        ws.onclose = function (evt) {
            console.log("Closing connection. Bye!", evt);
        };

        ws.onerror = function (evt) {
            console.log("Error: " + evt.data);
        };

        ws.onmessage = function (evt) {
            var event = JSON.parse(evt.data);
            console.log('message received', event);
            if (!event.hasOwnProperty("type")) {
                console.log('Error: Incorrect event structure');
                return;
            }
            switch (event.type) {
                case 'init':
                    apiKey = event.apiKey;
                    map = L.map('map').setView(event.center).fitBounds(event.bounds);
                    L.rectangle(event.bounds, {color: "#ff7800", opacity: 0.3, weight: 1}).addTo(map);
                    L.tileLayer(`https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png?apiKey=${apiKey}`, {
                        attribution: '&copy; 2025 <a href="https://www.geoapify.com/">Geoapify</a>',
                        maxZoom: 15
                    }).addTo(map);
                    break;
                case 'show':
                    if (map === undefined) return; // Ignore message. Can't show anything before the map is initialized
                    map.eachLayer((layer) => {
                        if (layer.options.aircraftid === undefined) return;
                        if (layer.options.aircraftid in event.aircrafts) {
                            being_tracked.push(layer.options.aircraftid);
                            const aircraft = event.aircrafts[layer.options.aircraftid]
                            if (layer.latitude != aircraft.latitude || layer.longitude != aircraft.longitude) {
                                layer.setLatLng([aircraft.latitude, aircraft.longitude])
                                var icon;
                                if (aircraft.flying) icon = flyingIcon;
                                else icon = landedIcon;
                                layer.setIcon(icon)
                            }
                        }
                    });
                    for (const [id, aircraft] of Object.entries(event.aircrafts)) {
                        if (!being_tracked.includes(id)) {
                            L.marker([aircraft.latitude, aircraft.longitude], {
                                alt: id,
                                aircraftid: id,
                                flyingIcon: flyingIcon
                            }).addTo(map).bindPopup(popupText(aircraft));
                            console.log(id, 'new', aircraft.flying);
                        }
                    }
                    break;
                default:
                    console.log('Error: Incorrect event type');
            }
        };
    }
}