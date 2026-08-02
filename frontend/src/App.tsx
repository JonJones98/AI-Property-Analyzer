import { Route, Routes } from "react-router-dom";

import { Nav } from "./components/Nav";
import { DashboardPage } from "./pages/Dashboard";
import { ListingDetailPage } from "./pages/ListingDetail";
import { ListingsPage } from "./pages/Listings";
import { MapViewPage } from "./pages/MapView";

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/listings" element={<ListingsPage />} />
        <Route path="/listings/:id" element={<ListingDetailPage />} />
        <Route path="/map" element={<MapViewPage />} />
      </Routes>
    </div>
  );
}
