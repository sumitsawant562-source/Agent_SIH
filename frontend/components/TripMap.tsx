"use client";

import React, { useEffect, useRef, useState } from "react";

interface PlaceMarker {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
}

interface TripMapProps {
  userLocation?: { latitude: number; longitude: number } | null;
  destinationLocation?: {
    latitude: number;
    longitude: number;
    name?: string;
  } | null;
  routeGeometry?: [number, number][] | null;
  places?: PlaceMarker[];
  onSelectDestination?: (place: {
    latitude: number;
    longitude: number;
    name: string;
  }) => void;
  className?: string;
}

declare global {
  interface Window {
    L: any;
  }
}

export function TripMap({
  userLocation,
  destinationLocation,
  routeGeometry,
  places = [],
  onSelectDestination,
  className = "h-96 w-full rounded-2xl overflow-hidden",
}: TripMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);
  const routePolylineRef = useRef<any>(null);
  const [isLeafletReady, setIsLeafletReady] = useState(false);

  // 1. Dynamically load Leaflet script & stylesheet
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    if (window.L) {
      setIsLeafletReady(true);
      return;
    }

    const script = document.createElement("script");
    script.id = "leaflet-js";
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.async = true;
    script.onload = () => {
      setIsLeafletReady(true);
    };
    document.body.appendChild(script);
  }, []);

  // 2. Initialize Leaflet Map Instance
  useEffect(() => {
    if (!isLeafletReady || !mapContainerRef.current || mapInstanceRef.current) return;

    const L = window.L;
    if (!L) return;

    // Default center: Goa / India
    const initialLat = userLocation?.latitude || destinationLocation?.latitude || 15.4989;
    const initialLon = userLocation?.longitude || destinationLocation?.longitude || 73.8278;

    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      scrollWheelZoom: true,
    }).setView([initialLat, initialLon], 12);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [isLeafletReady]);

  // 3. Update Markers and Polyline Route on State Changes
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current || !window.L) return;

    const L = window.L;
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;

    layerGroup.clearLayers();
    if (routePolylineRef.current) {
      map.removeLayer(routePolylineRef.current);
      routePolylineRef.current = null;
    }

    const boundsPoints: [number, number][] = [];

    // Custom Icon Creators
    const createPulsingUserIcon = () =>
      L.divIcon({
        className: "user-gps-pulse-marker",
        html: `
          <div style="position: relative; width: 24px; height: 24px;">
            <div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; background: rgba(59, 130, 246, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="position: absolute; top: 4px; left: 4px; width: 16px; height: 16px; border-radius: 50%; background: #2563eb; border: 2px solid #ffffff; box-shadow: 0 0 8px rgba(37,99,235,0.8);"></div>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

    const createPlaceIcon = (color: string, label: string) =>
      L.divIcon({
        className: "custom-place-marker",
        html: `
          <div style="display: flex; flex-direction: column; align-items: center; cursor: pointer;">
            <div style="background: ${color}; color: #ffffff; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; border: 1.5px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.4); white-space: nowrap;">
              ${label}
            </div>
            <div style="width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid ${color};"></div>
          </div>
        `,
        iconSize: [80, 30],
        iconAnchor: [40, 30],
      });

    // A. Render Live GPS User Location
    if (userLocation && typeof userLocation.latitude === "number" && typeof userLocation.longitude === "number") {
      const userMarker = L.marker([userLocation.latitude, userLocation.longitude], {
        icon: createPulsingUserIcon(),
        zIndexOffset: 1000,
      }).addTo(layerGroup);

      userMarker.bindPopup(`
        <div style="font-size: 12px; font-family: sans-serif; padding: 4px;">
          <strong style="color: #2563eb;">📍 Your Current Location</strong><br/>
          Lat: ${userLocation.latitude.toFixed(4)}, Lon: ${userLocation.longitude.toFixed(4)}
        </div>
      `);
      boundsPoints.push([userLocation.latitude, userLocation.longitude]);
    }

    // B. Render Selected Destination Marker
    if (destinationLocation && typeof destinationLocation.latitude === "number") {
      const destMarker = L.marker([destinationLocation.latitude, destinationLocation.longitude], {
        icon: createPlaceIcon("#8b5cf6", destinationLocation.name || "Target Destination"),
        zIndexOffset: 900,
      }).addTo(layerGroup);

      destMarker.bindPopup(`
        <div style="font-size: 12px; font-family: sans-serif; padding: 4px;">
          <strong style="color: #8b5cf6;">🏁 ${destinationLocation.name || "Destination"}</strong><br/>
          Lat: ${destinationLocation.latitude.toFixed(4)}, Lon: ${destinationLocation.longitude.toFixed(4)}
        </div>
      `);
      boundsPoints.push([destinationLocation.latitude, destinationLocation.longitude]);
    }

    // C. Render Other Itinerary & Stage 5 Place Markers
    places.forEach((p) => {
      if (typeof p.latitude === "number" && typeof p.longitude === "number") {
        const isSelected =
          destinationLocation &&
          Math.abs(destinationLocation.latitude - p.latitude) < 0.0001 &&
          Math.abs(destinationLocation.longitude - p.longitude) < 0.0001;

        if (!isSelected) {
          const marker = L.marker([p.latitude, p.longitude], {
            icon: createPlaceIcon("#0ea5e9", p.name),
          }).addTo(layerGroup);

          marker.on("click", () => {
            if (onSelectDestination) {
              onSelectDestination(p);
            }
          });

          marker.bindPopup(`
            <div style="font-size: 12px; font-family: sans-serif; padding: 4px;">
              <strong>${p.name}</strong><br/>
              <span style="color: #64748b;">${p.category || "Attraction"}</span>
            </div>
          `);
          boundsPoints.push([p.latitude, p.longitude]);
        }
      }
    });

    // D. Render Turn-by-Turn Route Polyline
    if (routeGeometry && Array.isArray(routeGeometry) && routeGeometry.length > 0) {
      const polyline = L.polyline(routeGeometry, {
        color: "#8b5cf6",
        weight: 6,
        opacity: 0.85,
        smoothFactor: 1.0,
      }).addTo(map);

      routePolylineRef.current = polyline;

      try {
        const polyBounds = polyline.getBounds();
        if (polyBounds.isValid()) {
          map.fitBounds(polyBounds, { padding: [40, 40] });
          return;
        }
      } catch (err) {
        // Fallback to manual bounds
      }
    }

    // E. Auto-fit bounds if no polyline
    if (boundsPoints.length > 1) {
      map.fitBounds(boundsPoints, { padding: [50, 50] });
    } else if (boundsPoints.length === 1) {
      map.setView(boundsPoints[0], 13);
    }
  }, [userLocation, destinationLocation, routeGeometry, places, onSelectDestination]);

  return (
    <div className={`relative ${className} border border-slate-800 bg-slate-950/80`}>
      <div ref={mapContainerRef} className="h-full w-full z-0" />
      {!isLeafletReady && (
        <div className="absolute inset-0 bg-slate-900/90 flex items-center justify-center text-xs text-slate-400 gap-2">
          <div className="h-4 w-4 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
          <span>Loading Interactive Map...</span>
        </div>
      )}
    </div>
  );
}
