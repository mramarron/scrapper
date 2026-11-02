import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    'Accept': 'application/json',
  },

  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withCredentials: true,
});

export interface ScrapedListing {
  id: number;
  source_platform: string;
  vendor_name: string;
  phone_number: string | null;
  listing_title: string;
  item_price: string | null;
  location_district: string | null;
  category: string | null;
  listing_url: string;
  scraped_at: string;
}

export interface BusinessLead {
  id: number;
  business_name: string;
  category: string | null;
  location: string | null;
  phone_number: string;
  email: string;
  profile_url: string;
  scraped_at: string;
}

export default api;