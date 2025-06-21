import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import DealForm from "./components/DealForm";
import DealDetails from "./components/DealDetails";
import MenuSelling from "./components/MenuSelling";
import Navbar from "./components/Navbar";

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/deal/new" element={<DealForm />} />
            <Route path="/deal/:dealId" element={<DealDetails />} />
            <Route path="/deal/:dealId/menu" element={<MenuSelling />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;