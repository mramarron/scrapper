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

export interface ScrapeRun {
  id: string;
  status: "queued" | "running" | "completed" | "failed";
  error_code?:
    | "upstream_timeout"
    | "upstream_unreachable"
    | "upstream_rate_limited"
    | "upstream_access_denied"
    | "upstream_server_error"
    | "upstream_request_failed"
    | "directory_empty"
    | "storage_error"
    | "worker_unavailable"
    | "unexpected_error"
    | "";
  progress: {
    stage?: "starting" | "loading_directory" | "processing_businesses" | "completed";
    message?: string;
    current?: number;
    total?: number;
    businesses_processed?: number;
    businesses_added?: number;
    products_processed?: number;
    products_added?: number;
  };
  output: string;
  error: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export default api;